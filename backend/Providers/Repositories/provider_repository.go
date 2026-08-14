package Repositories

import (
	"context"
	"errors"
	"github.com/alumasinde/jijenge/Providers/Models"
	"math"
	"sync"
)

var ErrNotFound = errors.New("provider not found")

type Repository interface {
	UpsertProfile(context.Context, *Models.Profile) error
	UpsertLocation(context.Context, *Models.Location) error
	FindProfile(context.Context, uint64) (*Models.Profile, error)
	FindLocation(context.Context, uint64) (*Models.Location, error)
	Nearby(context.Context, float64, float64, float64) []Models.Location
}
type MemoryRepository struct {
	mu        sync.RWMutex
	profiles  map[uint64]*Models.Profile
	locations map[uint64]*Models.Location
}

func NewMemoryRepository() *MemoryRepository {
	return &MemoryRepository{profiles: map[uint64]*Models.Profile{}, locations: map[uint64]*Models.Location{}}
}
func (r *MemoryRepository) UpsertProfile(ctx context.Context, p *Models.Profile) error {
	if p.UserID == 0 {
		return ErrNotFound
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	r.profiles[p.UserID] = p
	return nil
}
func (r *MemoryRepository) UpsertLocation(ctx context.Context, l *Models.Location) error {
	if l.UserID == 0 || math.IsNaN(l.Latitude) || math.IsNaN(l.Longitude) || l.Latitude < -90 || l.Latitude > 90 || l.Longitude < -180 || l.Longitude > 180 {
		return errors.New("invalid coordinates")
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	r.locations[l.UserID] = l
	return nil
}
func (r *MemoryRepository) FindProfile(ctx context.Context, id uint64) (*Models.Profile, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	p, ok := r.profiles[id]
	if !ok {
		return nil, ErrNotFound
	}
	x := *p
	return &x, nil
}
func (r *MemoryRepository) FindLocation(ctx context.Context, id uint64) (*Models.Location, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	l, ok := r.locations[id]
	if !ok {
		return nil, ErrNotFound
	}
	x := *l
	return &x, nil
}
func (r *MemoryRepository) Nearby(ctx context.Context, lat, lon, radius float64) []Models.Location {
	r.mu.RLock()
	defer r.mu.RUnlock()
	out := []Models.Location{}
	for _, l := range r.locations {
		if distance(lat, lon, l.Latitude, l.Longitude) <= radius {
			out = append(out, *l)
		}
	}
	return out
}
func distance(a, b, c, d float64) float64 {
	const R = 6371
	rad := math.Pi / 180
	dlat := (c - a) * rad
	dlon := (d - b) * rad
	x := math.Sin(dlat/2)*math.Sin(dlat/2) + math.Cos(a*rad)*math.Cos(c*rad)*math.Sin(dlon/2)*math.Sin(dlon/2)
	return 2 * R * math.Asin(math.Sqrt(x))
}
