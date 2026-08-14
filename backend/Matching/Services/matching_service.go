package Services

import (
	"context"
	"github.com/alumasinde/jijenge/Matching/Models"
	providerRepo "github.com/alumasinde/jijenge/Providers/Repositories"
	"math"
	"sort"
)

type Service struct{ Providers providerRepo.Repository }

func New(p providerRepo.Repository) *Service { return &Service{Providers: p} }
func (s *Service) Nearby(ctx context.Context, q Models.Request) []Models.Candidate {
	locs := s.Providers.Nearby(ctx, q.Latitude, q.Longitude, q.RadiusKM)
	out := make([]Models.Candidate, 0, len(locs))
	for _, l := range locs {
		d := haversine(q.Latitude, q.Longitude, l.Latitude, l.Longitude)
		out = append(out, Models.Candidate{UserID: l.UserID, DistanceKM: d})
	}
	sort.Slice(out, func(i, j int) bool { return out[i].DistanceKM < out[j].DistanceKM })
	return out
}
func haversine(a, b, c, d float64) float64 {
	const R = 6371
	rad := math.Pi / 180
	la, lc := a*rad, c*rad
	dl := (c - a) * rad
	dn := (d - b) * rad
	x := math.Sin(dl/2)*math.Sin(dl/2) + math.Cos(la)*math.Cos(lc)*math.Sin(dn/2)*math.Sin(dn/2)
	return 2 * R * math.Asin(math.Sqrt(x))
}
