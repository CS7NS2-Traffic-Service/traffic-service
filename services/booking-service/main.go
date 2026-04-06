package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/lukaslinss98/booking-service/internal/application"
	"github.com/lukaslinss98/booking-service/internal/infrastructure/handler"
	"github.com/lukaslinss98/booking-service/internal/infrastructure/postgres"
	"github.com/lukaslinss98/booking-service/internal/infrastructure/redisconsumer"
	"github.com/lukaslinss98/booking-service/internal/infrastructure/redisproducer"
	"github.com/redis/go-redis/v9"
)

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	hostname, err := os.Hostname()
	if err != nil {
		log.Fatal("failed to get hostname: ", err)
	}

	pool := createDbPool()
	defer pool.Close()

	redisClient := createRediClient()
	eventPublisher := redisproducer.NewEventPublisher(redisClient)
	bookingRepository := postgres.NewBookingRepository(pool)
	bookingService := application.NewBookingService(bookingRepository, eventPublisher)
	bookingHandler := handler.NewBookingHandler(bookingService)
	consumer := redisconsumer.NewConsumer(hostname, redisClient, bookingService, bookingRepository)

	go consumer.Start(ctx)
	go bookingService.StartExpiryLoop(ctx)

	router := chi.NewRouter()

	router.Get("/health", healthCheckHandler)
	router.Get("/health/live", healthLiveHandler)
	router.Get("/health/ready", healthReadyHandler(pool, redisClient))
	router.Route("/api/booking/bookings", func(r chi.Router) {
		r.Get("/", bookingHandler.ListBookings)
		r.Post("/", bookingHandler.CreateBooking)
		r.Get("/{booking_id}", bookingHandler.GetBooking)
		r.Delete("/{booking_id}", bookingHandler.CancelBooking)
	})

	log.Println("booking service starting on :8082")

	server := &http.Server{
		Addr:    ":8082",
		Handler: router,
	}

	go func() {
		<-ctx.Done()
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		if err := server.Shutdown(shutdownCtx); err != nil {
			log.Printf("booking service shutdown error: %v", err)
		}
	}()

	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatal(err)
	}
}

func healthCheckHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status" : "ok"}`))
}

func healthLiveHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status":"live"}`))
}

func healthReadyHandler(pool *pgxpool.Pool, redisClient *redis.Client) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
		defer cancel()

		if err := pool.Ping(ctx); err != nil {
			http.Error(w, `{"status":"not_ready","dependency":"postgres"}`, http.StatusServiceUnavailable)
			return
		}

		if err := redisClient.Ping(ctx).Err(); err != nil {
			http.Error(w, `{"status":"not_ready","dependency":"redis"}`, http.StatusServiceUnavailable)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"status":"ready"}`))
	}
}

func createDbPool() *pgxpool.Pool {
	DATABASE_URL := os.Getenv("DATABASE_URL")

	ctx := context.Background()

	pool, err := pgxpool.New(ctx, DATABASE_URL)
	if err != nil {
		log.Fatal(err)
	}

	if err := pool.Ping(ctx); err != nil {
		log.Fatal("failed to ping database: ", err)
	}
	log.Println("connected to database")

	return pool
}

func createRediClient() *redis.Client {
	opts, err := redis.ParseURL(os.Getenv("REDIS_URL"))
	if err != nil {
		log.Fatal(err)
	}
	return redis.NewClient(opts)
}
