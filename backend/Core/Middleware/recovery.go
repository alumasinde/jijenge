package Middleware

import (
	"log/slog"
	"net/http"

	"github.com/alumasinde/jijenge/Core/HTTP"
)

func Recovery(logger *slog.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			defer func() {
				if recovered := recover(); recovered != nil {
					logger.Error("panic recovered",
						"panic", recovered,
						"request_id", GetRequestID(r.Context()),
					)
					HTTP.ErrorResponse(w, http.StatusInternalServerError,
						"INTERNAL_SERVER_ERROR",
						"An internal server error occurred")
				}
			}()
			next.ServeHTTP(w, r)
		})
	}
}
