package redisconsumer

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/lukaslinss98/booking-service/internal/application"
	"github.com/lukaslinss98/booking-service/internal/domain"
	"github.com/redis/go-redis/v9"
)

type Consumer struct {
	hostname string
	client   *redis.Client
	service  *application.BookingService
	repo     application.BookingRepository
}

func NewConsumer(
	hostname string,
	client *redis.Client,
	service *application.BookingService,
	repo application.BookingRepository,
) *Consumer {
	return &Consumer{
		hostname: hostname,
		client:   client,
		service:  service,
		repo:     repo,
	}
}

func (c *Consumer) ensureConsumerGroup(ctx context.Context) {
	for {
		if ctx.Err() != nil {
			return
		}
		err := c.client.XGroupCreateMkStream(ctx, "route.assessed", "booking-service", "0").Err()
		if err == nil || strings.Contains(err.Error(), "BUSYGROUP") {
			return
		}
		log.Printf("failed to create consumer group, retrying in 2s: %v", err)
		time.Sleep(2 * time.Second)
	}
}

func (c *Consumer) Start(ctx context.Context) {
	c.ensureConsumerGroup(ctx)

	for {
		if ctx.Err() != nil {
			return
		}

		messages, err := c.client.XReadGroup(ctx,
			&redis.XReadGroupArgs{
				Group:    "booking-service",
				Consumer: c.hostname,
				Streams:  []string{"route.assessed", ">"},
				Count:    10,
				Block:    5000 * time.Millisecond,
			}).Result()

		if err != nil {
			if errors.Is(err, context.Canceled) || errors.Is(err, context.DeadlineExceeded) {
				return
			}
			if errors.Is(err, redis.Nil) {
				continue
			}
			if strings.Contains(err.Error(), "NOGROUP") {
				c.ensureConsumerGroup(ctx)
				continue
			}
			log.Printf("consumer error: %v", err)
			time.Sleep(time.Second)
			continue
		}

		for _, stream := range messages {
			for _, msg := range stream.Messages {
				if err := c.handleMessageWithRetry(ctx, stream.Stream, msg); err != nil {
					log.Printf("failed to handle message %s: %v", msg.ID, err)
					c.sendToDLQ(ctx, stream.Stream, msg, err)
					c.client.XAck(ctx, stream.Stream, "booking-service", msg.ID)
					continue
				}
				c.client.XAck(ctx, stream.Stream, "booking-service", msg.ID)
			}
		}
	}

}

func (c *Consumer) handleMessageWithRetry(ctx context.Context, stream string, message redis.XMessage) error {
	var lastErr error
	for attempt := 1; attempt <= 3; attempt++ {
		if err := c.handleMessage(ctx, stream, message); err != nil {
			lastErr = err
			backoff := time.Duration(attempt*attempt) * 200 * time.Millisecond
			time.Sleep(backoff)
			continue
		}
		return nil
	}
	return lastErr
}

func (c *Consumer) handleMessage(ctx context.Context, stream string, message redis.XMessage) error {
	dataStr, ok := message.Values["data"].(string)
	if !ok {
		return fmt.Errorf("missing or invalid 'data' field in message %s", message.ID)
	}

	envelope, event, err := parseEvent(dataStr, stream, message.ID)
	if err != nil {
		return err
	}

	alreadyProcessed, err := c.repo.IsEventProcessed(ctx, envelope.EventID, "booking-service")
	if err != nil {
		return err
	}
	if alreadyProcessed {
		return nil
	}

	eventCtx := domain.ContextWithCorrelationID(ctx, envelope.CorrelationID)
	if err := c.service.HandleRouteAssessed(eventCtx, event); err != nil {
		return err
	}

	if _, err := c.repo.MarkEventProcessed(ctx, envelope.EventID, "booking-service", stream); err != nil {
		return err
	}

	return nil
}

func (c *Consumer) sendToDLQ(ctx context.Context, stream string, msg redis.XMessage, err error) {
	dlqPayload := map[string]any{
		"stream":    stream,
		"messageId": msg.ID,
		"values":    msg.Values,
		"error":     err.Error(),
		"failed_at": time.Now().UTC().Format(time.RFC3339Nano),
	}

	data, marshalErr := json.Marshal(dlqPayload)
	if marshalErr != nil {
		log.Printf("failed to marshal DLQ message: %v", marshalErr)
		return
	}

	if dlqErr := c.client.XAdd(ctx, &redis.XAddArgs{
		Stream: stream + ".dlq",
		Values: map[string]any{
			"data": string(data),
		},
	}).Err(); dlqErr != nil {
		log.Printf("failed to publish DLQ message: %v", dlqErr)
	}
}

func parseEvent(dataStr string, stream string, messageID string) (*domain.EventEnvelope, domain.RouteAssessedEvent, error) {
	var envelope domain.EventEnvelope
	if err := json.Unmarshal([]byte(dataStr), &envelope); err == nil {
		if envelope.EventID != "" {
			payload, err := json.Marshal(envelope.Data)
			if err != nil {
				return nil, domain.RouteAssessedEvent{}, err
			}

			var event domain.RouteAssessedEvent
			if err := json.Unmarshal(payload, &event); err != nil {
				return nil, domain.RouteAssessedEvent{}, err
			}
			return &envelope, event, nil
		}
	}

	var event domain.RouteAssessedEvent
	if err := json.Unmarshal([]byte(dataStr), &event); err != nil {
		return nil, domain.RouteAssessedEvent{}, err
	}

	fallbackEnvelope := &domain.EventEnvelope{
		EventID:       uuid.NewString(),
		CorrelationID: "",
		EventType:     stream,
		CreatedAt:     time.Now().UTC(),
		Data:          event,
	}
	if messageID != "" {
		fallbackEnvelope.EventID = fmt.Sprintf("%s:%s", stream, messageID)
	}
	return fallbackEnvelope, event, nil
}
