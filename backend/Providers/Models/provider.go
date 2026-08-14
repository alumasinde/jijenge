package Models

import "time"

type Profile struct {
	UserID               uint64
	DisplayName, Bio     string
	ServiceRadiusKM      float64
	Verified             bool
	CreatedAt, UpdatedAt time.Time
}
type Location struct {
	UserID                      uint64
	Country, County, City, Area string
	Latitude, Longitude         float64
	UpdatedAt                   time.Time
}
type Skill struct {
	ServiceID uint64
	Name      string
}
