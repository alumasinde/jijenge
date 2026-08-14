package Repositories

import (
	"context"
	"github.com/alumasinde/jijenge/Ratings/Models"
	"testing"
)

func TestOneRatingPerAssignmentAndNoSelf(t *testing.T) {
	r := NewMemoryRepository()
	if e := r.Create(context.Background(), &Models.Rating{AssignmentID: 1, ReviewerUserID: 2, RevieweeUserID: 2, Score: 5, Status: "published"}); e != ErrInvalid {
		t.Fatal(e)
	}
	x := &Models.Rating{AssignmentID: 1, ReviewerUserID: 2, RevieweeUserID: 3, Score: 5, Status: "published"}
	if e := r.Create(context.Background(), x); e != nil {
		t.Fatal(e)
	}
	if e := r.Create(context.Background(), &Models.Rating{AssignmentID: 1, ReviewerUserID: 2, RevieweeUserID: 3, Score: 4, Status: "published"}); e != ErrDuplicate {
		t.Fatal(e)
	}
}
