package main

import (
	"context"
	"errors"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	jijenge "github.com/alumasinde/jijenge"
	"github.com/alumasinde/jijenge/Core/Config"
)

func main() {
	cfg := Config.Load()
	if err := cfg.Validate(); err != nil {
		panic(err)
	}
	app := jijenge.NewApp(cfg)

	server := &http.Server{
		Addr:              cfg.Host + ":" + cfg.Port,
		Handler:           app.Router,
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       cfg.ReadTimeout,
		WriteTimeout:      cfg.WriteTimeout,
		IdleTimeout:       cfg.IdleTimeout,
		MaxHeaderBytes:    1 << 20,
	}

	serverErr := make(chan error, 1)
	go func() {
		app.Logger.Info("starting Jijenge API",
			"address", server.Addr,
			"environment", cfg.Environment,
		)
		serverErr <- server.ListenAndServe()
	}()

	shutdownSignal := make(chan os.Signal, 1)
	signal.Notify(shutdownSignal, syscall.SIGINT, syscall.SIGTERM)
	defer signal.Stop(shutdownSignal)

	select {
	case err := <-serverErr:
		if !errors.Is(err, http.ErrServerClosed) {
			app.Logger.Error("server failed", "error", err)
			os.Exit(1)
		}
	case sig := <-shutdownSignal:
		app.Logger.Info("shutdown signal received", "signal", sig.String())
	}

	ctx, cancel := context.WithTimeout(context.Background(), cfg.ShutdownTimeout)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		app.Logger.Error("graceful shutdown failed", "error", err)
		os.Exit(1)
	}

	app.Logger.Info("Jijenge API stopped")
}
