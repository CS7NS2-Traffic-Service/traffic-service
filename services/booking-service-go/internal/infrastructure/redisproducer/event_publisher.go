package redisproducer

import (
	"context"
	"encoding/json"
	"log"

	"github.com/lukaslinss98/booking-service/internal/domain"
	"github.com/redis/go-redis/v9"
)

type EventPublisher struct {
	client *redis.Client
}

func NewEventPublisher(client *redis.Client) *EventPublisher {
	return &EventPublisher{
		client: client,
	}
}

func (ep *EventPublisher) Publish(ctx context.Context, event domain.Event) error {
	data, err := json.Marshal(event)
	if err != nil {
		log.Printf("failed to marshal event %s: %v", event.Stream(), err)
		return err
	}

	if err := ep.client.XAdd(ctx, &redis.XAddArgs{
		Stream: event.Stream(),
		Values: map[string]any{"data": string(data)},
	}).Err(); err != nil {
		log.Printf("failed to publish event %s: %v", event.Stream(), err)
		return err
	}

	log.Printf("published event %s", event.Stream())
	return nil
}
