package domain

type BookingStatus string

const (
	StatusPending   BookingStatus = "PENDING"
	StatusApproved  BookingStatus = "APPROVED"
	StatusRejected  BookingStatus = "REJECTED"
	StatusCancelled BookingStatus = "CANCELLED"
	StatusExpired   BookingStatus = "EXPIRED"
)
