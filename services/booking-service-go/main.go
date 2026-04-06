package main

import (
	"context"
	"log"
	"net/http"
	"os"

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
	consumer := redisconsumer.NewConsumer(hostname, redisClient, bookingService)

	go consumer.Start(context.Background())
	go bookingService.StartExpiryLoop(context.Background())

	router := chi.NewRouter()

	router.Get("/health", healthCheckHandler)
	router.Route("/api/booking/bookings", func(r chi.Router) {
		r.Get("/", bookingHandler.ListBookings)
		r.Post("/", bookingHandler.CreateBooking)
		r.Get("/{booking_id}", bookingHandler.GetBooking)
		r.Delete("/{booking_id}", bookingHandler.CancelBooking)
	})

	log.Println("booking service starting on :8082")

	if err := http.ListenAndServe(":8082", router); err != nil {
		log.Fatal(err)
	}
}

func healthCheckHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status" : "ok"}`))
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
