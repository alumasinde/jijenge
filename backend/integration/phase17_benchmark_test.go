package integration

import (
	"fmt"
	"github.com/alumasinde/jijenge/Core/Middleware"
	"testing"
	"time"
)

func BenchmarkRateLimiter(b *testing.B) {
	l := Middleware.NewRateLimiter(100, time.Minute, b.N+100)
	now := time.Now()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		if !l.Allow(fmt.Sprintf("bench-%d", i), now) {
			b.Fatal("unexpected limit")
		}
	}
}
