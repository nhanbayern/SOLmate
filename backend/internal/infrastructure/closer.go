package infrastructure

import (
	"log/slog"
	"sync"
)

type AppCloser struct {
	mu    sync.Mutex
	funcs []func() error
	log   *slog.Logger
}

func NewAppCloser(logger *slog.Logger) *AppCloser {
	return &AppCloser{
		log: logger,
	}
}

func (c *AppCloser) Add(f func() error) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.funcs = append(c.funcs, f)
}

func (c *AppCloser) CloseAll() {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.log.Info("Shutting down resources")

	for i := len(c.funcs) - 1; i >= 0; i-- {
		if err := c.funcs[i](); err != nil {
			c.log.Warn(
				"Resource close failed",
				KeyError, err.Error(),
			)
		}
	}

	c.log.Info("All resources closed")
}
