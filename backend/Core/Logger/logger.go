package Logger

import (
	"log/slog"
	"os"
)

type Logger struct {
	*slog.Logger
}

func New(environment string) *Logger {
	var handler slog.Handler
	options := &slog.HandlerOptions{Level: slog.LevelInfo}

	if environment != "production" {
		options.Level = slog.LevelDebug
		handler = slog.NewTextHandler(os.Stdout, options)
	} else {
		handler = slog.NewJSONHandler(os.Stdout, options)
	}

	return &Logger{Logger: slog.New(handler)}
}
