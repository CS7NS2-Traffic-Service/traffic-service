package application

import (
	"context"

	"github.com/lukaslinss98/booking-service/internal/domain"
)

type EventPublisher interface {
	Publish(ctx context.Context, event domain.Event) error
}
