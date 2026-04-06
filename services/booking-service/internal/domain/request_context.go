package domain

import (
	"context"

	"github.com/google/uuid"
)

type ctxKey string

const correlationIDCtxKey ctxKey = "correlation_id"

func CorrelationIDFromContext(ctx context.Context) string {
	if value, ok := ctx.Value(correlationIDCtxKey).(string); ok && value != "" {
		return value
	}
	return uuid.NewString()
}

func ContextWithCorrelationID(ctx context.Context, correlationID string) context.Context {
	if correlationID == "" {
		return context.WithValue(ctx, correlationIDCtxKey, uuid.NewString())
	}
	return context.WithValue(ctx, correlationIDCtxKey, correlationID)
}
