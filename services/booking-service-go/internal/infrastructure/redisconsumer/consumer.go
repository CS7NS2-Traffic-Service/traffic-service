package redisconsumer

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"strings"
	"time"

	"github.com/lukaslinss98/booking-service/internal/application"
	"github.com/lukaslinss98/booking-service/internal/domain"
	"github.com/redis/go-redis/v9"
)

type Consumer struct {
	hostname string
	client   *redis.Client
	service  *application.BookingService
}

func NewConsumer(hostname string, client *redis.Client, service *application.BookingService) *Consumer {
	return &Consumer{
		hostname: hostname,
		client:   client,
		service:  service,
	}
}

func (c *Consumer) Start(ctx context.Context) {
	err := c.client.XGroupCreateMkStream(ctx, "route.assessed", "booking-service", "0").Err()

	if err != nil && !strings.Contains(err.Error(),
		"BUSYGROUP") {
		log.Fatal("failed to create consumer group: ", err)
	}

	for {
		messages, err := c.client.XReadGroup(ctx,
			&redis.XReadGroupArgs{
				Group:    "booking-service",
				Consumer: c.hostname,
				Streams:  []string{"route.assessed", ">"},
				Count:    10,
				Block:    5000 * time.Millisecond,
			}).Result()

		if err != nil {
			if errors.Is(err, redis.Nil) {
				continue
			}
			log.Printf("consumer error: %v", err)
			continue
		}

		for _, stream := range messages {
			for _, msg := range stream.Messages {
				if err := c.handleMessage(ctx, msg); err != nil {
					log.Printf("failed to handle message %s: %v", msg.ID, err)
					continue
				}
				c.client.XAck(ctx, "route.assessed", "booking-service", msg.ID)
			}
		}
	}

}

func (c *Consumer) handleMessage(ctx context.Context, message redis.XMessage) error {
	dataStr, ok := message.Values["data"].(string)
	if !ok {
		return fmt.Errorf("missing or invalid 'data' field in message %s", message.ID)
	}

	var event domain.RouteAssessedEvent
	if err := json.Unmarshal([]byte(dataStr), &event); err != nil {
		return err
	}

	if err := c.service.HandleRouteAssessed(ctx, event); err != nil {
		return err
	}

	return nil
}
