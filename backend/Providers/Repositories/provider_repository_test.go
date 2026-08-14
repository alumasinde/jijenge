package Repositories

import (
	"context"
	"github.com/alumasinde/jijenge/Providers/Models"
	"testing"
)

func TestCoordinateValidation(t *testing.T) {
	r := NewMemoryRepository()
	if e := r.UpsertLocation(context.Background(), &Models.Location{UserID: 1, Country: "KE", Latitude: 100, Longitude: 36}); e == nil {
		t.Fatal("invalid latitude accepted")
	}
}
