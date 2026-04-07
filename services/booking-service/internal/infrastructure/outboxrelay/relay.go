package outboxrelay

import (
	"context"
	"log"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/lukaslinss98/booking-service/internal/infrastructure/postgres"
	"github.com/redis/go-redis/v9"
)

type Relay struct {
	pool      *pgxpool.Pool
	outbox    *postgres.OutboxRepository
	redis     *redis.Client
	interval  time.Duration
	batchSize int
}

func NewRelay(pool *pgxpool.Pool, outbox *postgres.OutboxRepository, redisClient *redis.Client) *Relay {
	return &Relay{
		pool:      pool,
		outbox:    outbox,
		redis:     redisClient,
		interval:  500 * time.Millisecond,
		batchSize: 50,
	}
}

func (r *Relay) Start(ctx context.Context) {
	log.Println("outbox relay started (polling every 500ms)")
	for {
		if ctx.Err() != nil {
			return
		}
		published, err := r.publishBatch(ctx)
		if err != nil {
			log.Printf("outbox relay error: %v", err)
		}
		if published < r.batchSize {
			select {
			case <-ctx.Done():
				return
			case <-time.After(r.interval):
			}
		}
	}
}

func (r *Relay) publishBatch(ctx context.Context) (int, error) {
	tx, err := r.pool.Begin(ctx)
	if err != nil {
		return 0, err
	}
	defer tx.Rollback(ctx)

	events, err := r.outbox.FetchUnpublished(ctx, tx, r.batchSize)
	if err != nil {
		return 0, err
	}
	if len(events) == 0 {
		return 0, nil
	}

	var publishedIDs []int64
	for _, evt := range events {
		err := r.redis.XAdd(ctx, &redis.XAddArgs{
			Stream: evt.Stream,
			Values: map[string]any{"data": string(evt.Payload)},
		}).Err()
		if err != nil {
			log.Printf("relay: failed to publish event %d to %s: %v", evt.ID, evt.Stream, err)
			break
		}
		publishedIDs = append(publishedIDs, evt.ID)
	}

	if len(publishedIDs) > 0 {
		if err := r.outbox.MarkPublished(ctx, tx, publishedIDs); err != nil {
			return 0, err
		}
	}

	if err := tx.Commit(ctx); err != nil {
		return 0, err
	}
	return len(publishedIDs), nil
}

func (r *Relay) StartCleanup(ctx context.Context) {
	ticker := time.NewTicker(1 * time.Hour)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			cutoff := time.Now().Add(-7 * 24 * time.Hour)
			deleted, err := r.outbox.DeleteOldPublished(ctx, r.pool, cutoff)
			if err != nil {
				log.Printf("outbox cleanup error: %v", err)
			} else if deleted > 0 {
				log.Printf("outbox cleanup: deleted %d old events", deleted)
			}
		}
	}
}
