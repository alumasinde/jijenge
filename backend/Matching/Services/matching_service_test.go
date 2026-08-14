package Services

import (
	"context"
	matchmodels "github.com/alumasinde/jijenge/Matching/Models"
	providermodels "github.com/alumasinde/jijenge/Providers/Models"
	"github.com/alumasinde/jijenge/Providers/Repositories"
	"testing"
)

func TestNearbyOrdering(t *testing.T) {
	r := Repositories.NewMemoryRepository()
	_ = r.UpsertLocation(context.Background(), &providermodels.Location{UserID: 1, Latitude: -1.286, Longitude: 36.817, Country: "KE"})
	_ = r.UpsertLocation(context.Background(), &providermodels.Location{UserID: 2, Latitude: -1.30, Longitude: 36.78, Country: "KE"})
	m := New(r)
	x := m.Nearby(context.Background(), matchmodels.Request{Latitude: -1.286, Longitude: 36.817, RadiusKM: 10})
	if len(x) != 2 || x[0].UserID != 1 {
		t.Fatalf("%+v", x)
	}
}
