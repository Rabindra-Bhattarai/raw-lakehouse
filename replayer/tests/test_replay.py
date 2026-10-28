"""Unit tests for the replay logic. No database or CSV files needed."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from replay import build_timeline, order_to_events, review_to_events  # noqa: E402


def make_order(order_id="o1", status="delivered", purchased="2017-10-02 10:56:33",
               approved="2017-10-02 11:07:15", shipped="2017-10-04 19:55:00",
               delivered="2017-10-10 21:25:13"):
    return pd.Series({
        "order_id": order_id,
        "order_status": status,
        "order_purchase_timestamp": purchased,
        "order_approved_at": approved,
        "order_delivered_carrier_date": shipped,
        "order_delivered_customer_date": delivered,
    })


def statuses(events):
    return [event[1] for event in events]


def test_delivered_order_has_four_events_in_story_order():
    events = order_to_events(make_order())
    assert statuses(events) == ["placed", "approved", "shipped", "delivered"]


def test_cancelled_order_ends_with_exactly_one_cancel():
    events = order_to_events(make_order(status="canceled", shipped=None, delivered=None))
    assert statuses(events) == ["placed", "approved", "canceled"]


def test_missing_dates_are_skipped():
    events = order_to_events(make_order(status="created", approved=None, shipped=None, delivered=None))
    assert statuses(events) == ["placed"]


def test_time_never_goes_backwards():
    # Real Olist quirk: shipped before approved.
    events = order_to_events(make_order(approved="2017-05-10 14:00:00", shipped="2017-05-10 09:00:00",
                                        purchased="2017-05-10 08:00:00", delivered=None, status="shipped"))
    times = [event[0] for event in events]
    assert times == sorted(times)


def test_review_cannot_come_before_its_order():
    review = {"review_creation_date": "2017-01-01 00:00:00", "review_answer_timestamp": None}
    events = review_to_events(review, 0, placed_at="2017-03-01 12:00:00")
    assert events == [("2017-03-01 12:00:00", "review", 0)]


def test_answered_review_has_two_events():
    review = {"review_creation_date": "2017-10-11 00:00:00", "review_answer_timestamp": "2017-10-12 03:43:48"}
    assert statuses(review_to_events(review, 7, placed_at="2017-10-02 10:56:33")) == ["review", "review_answered"]


def test_timeline_is_sorted_and_placed_comes_first_on_ties():
    orders = pd.DataFrame([
        make_order("a", purchased="2017-01-01 10:00:00", approved="2017-01-01 10:00:00",
                   shipped=None, delivered=None, status="approved"),
        make_order("b", purchased="2017-01-01 09:00:00", approved=None,
                   shipped=None, delivered=None, status="created"),
    ]).set_index("order_id", drop=False)
    timeline = build_timeline(orders, reviews=[])
    assert [(e[1], e[2]) for e in timeline] == [("placed", "b"), ("placed", "a"), ("approved", "a")]
