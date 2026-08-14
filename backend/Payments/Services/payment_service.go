package Services

import (
	"context"
	"crypto/sha256"
	"encoding/json"
	"errors"
	"strings"
	"time"

	"github.com/alumasinde/jijenge/Core/Security"
	financialrepo "github.com/alumasinde/jijenge/Financial/Repositories"
	"github.com/alumasinde/jijenge/Payments/Models"
	"github.com/alumasinde/jijenge/Payments/Provider"
	paymentrepo "github.com/alumasinde/jijenge/Payments/Repositories"
)

var (
	ErrInvalidPayment        = errors.New("invalid payment")
	ErrProviderEventConflict = errors.New("provider event conflict")
)

type Service struct {
	Payments          paymentrepo.Repository
	Ledger            financialrepo.LedgerRepository
	Provider          Provider.Verifier
	ClearingAccountID uint64
	Now               func() time.Time
}

type IncomingEvent struct {
	EventID     string `json:"event_id"`
	PaymentRef  string `json:"payment_ref"`
	Status      string `json:"status"`
	AmountCents int64  `json:"amount_cents"`
	Currency    string `json:"currency"`
}

func New(payments paymentrepo.Repository, ledger financialrepo.LedgerRepository, provider Provider.Verifier) *Service {
	return &Service{Payments: payments, Ledger: ledger, Provider: provider, Now: time.Now}
}
func (s *Service) SetClearingAccountID(id uint64) { s.ClearingAccountID = id }

func (s *Service) CreatePayment(ctx context.Context, provider, ref string, account uint64, amount int64, currency string) (*Models.Payment, error) {
	provider = strings.TrimSpace(provider)
	ref = strings.TrimSpace(ref)
	currency = strings.ToUpper(strings.TrimSpace(currency))
	if provider == "" || ref == "" || len(ref) > 128 || account == 0 || amount <= 0 || len(currency) != 3 {
		return nil, ErrInvalidPayment
	}
	now := s.Now()
	p := &Models.Payment{PublicID: paymentID(), Provider: provider, ProviderRef: ref, AccountID: account, AmountCents: amount, Currency: currency, Status: Models.StatusPending, CreatedAt: now, UpdatedAt: now}
	if err := s.Payments.CreatePayment(ctx, p); err != nil {
		return nil, err
	}
	return p, nil
}

// HandleWebhook verifies authenticity before parsing/acting on the provider event.
// The normalized provider event is intentionally small: no arbitrary provider JSON
// is trusted by the financial layer.
func (s *Service) HandleWebhook(ctx context.Context, payload []byte, signature string) (bool, error) {
	if s.Provider == nil || !s.Provider.Verify(payload, signature) {
		return false, Provider.ErrInvalidSignature
	}
	var ev IncomingEvent
	if err := json.Unmarshal(payload, &ev); err != nil {
		return false, ErrInvalidPayment
	}
	ev.EventID = strings.TrimSpace(ev.EventID)
	ev.PaymentRef = strings.TrimSpace(ev.PaymentRef)
	ev.Currency = strings.ToUpper(strings.TrimSpace(ev.Currency))
	if ev.EventID == "" || len(ev.EventID) > 128 || ev.PaymentRef == "" || ev.AmountCents <= 0 || len(ev.Currency) != 3 {
		return false, ErrInvalidPayment
	}
	hash := sha256.Sum256(payload)
	we := &Models.WebhookEvent{Provider: s.Provider.Name(), EventID: ev.EventID, PaymentRef: ev.PaymentRef, AmountCents: ev.AmountCents, Currency: ev.Currency, Signature: signature, PayloadHash: hash, CreatedAt: s.Now()}
	processed, err := s.Payments.RecordWebhook(ctx, we)
	if err != nil {
		return false, err
	}
	if processed {
		return true, nil
	}
	p, err := s.Payments.GetPaymentByProviderRef(ctx, s.Provider.Name(), ev.PaymentRef)
	if err != nil {
		return false, err
	}
	if p.AmountCents != ev.AmountCents || p.Currency != ev.Currency {
		return false, ErrProviderEventConflict
	}
	switch strings.ToLower(ev.Status) {
	case "success", "confirmed", "paid":
		if s.ClearingAccountID != 0 {
			if err := s.Payments.ConfirmAndSettlePayment(ctx, p.ID, ev.PaymentRef, ev.EventID, s.ClearingAccountID, "payment:"+s.Provider.Name()+":"+ev.EventID, s.Now()); err != nil {
				return false, err
			}
		} else if err := s.Payments.ConfirmPayment(ctx, p.ID, ev.PaymentRef, ev.EventID, s.Now()); err != nil {
			return false, err
		}
	case "failed", "cancelled":
		if err := s.Payments.FailPayment(ctx, p.ID, ev.Status, s.Now()); err != nil {
			return false, err
		}
	default:
		return false, ErrInvalidPayment
	}
	if err := s.Payments.MarkWebhookProcessed(ctx, we.ID, s.Now()); err != nil {
		return false, err
	}
	return false, nil
}
func paymentID() string {
	b, err := Security.GenerateToken(32)
	if err != nil {
		panic(err)
	}
	return b[:26]
}
