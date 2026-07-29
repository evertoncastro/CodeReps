# Level 4 Requirements

Agents want to follow tickets and be notified when they change. Extend the
**same** `TicketSystem` class.

An agent can **watch** a ticket. Whenever a watched ticket undergoes a
**successful status transition** (`assign`, `resolve`, `close`, or `reopen`),
every agent currently watching that ticket receives a notification recording the
new status.

A notification is the string `"<ticket_id>:<new_status>"` — for example
`"t1:in_progress"` when `t1` is assigned.

## New methods

### `watch(ticket_id: str, agent_id: str) -> bool`

Subscribe `agent_id` to `ticket_id`.

- Returns `True` on success.
- Returns `False`, changing nothing, if the ticket does not exist or `agent_id`
  is already watching it.

### `unwatch(ticket_id: str, agent_id: str) -> bool`

Unsubscribe `agent_id` from `ticket_id`.

- Returns `True` on success.
- Returns `False`, changing nothing, if the ticket does not exist or `agent_id`
  is not currently watching it.
- Past notifications the agent already received are **not** removed.

### `notifications(agent_id: str) -> list[str]`

Return the list of notifications delivered to `agent_id`, in the order they
occurred (oldest first).

- Returns an empty list if the agent has received none.

## Notification rules

- Only **successful** transitions notify; a rejected transition (one that returns
  `False`) notifies nobody.
- A notification is delivered only to agents watching the ticket **at the moment
  of the transition**. An agent who watches after a transition does not receive
  that past transition; an agent who unwatches before a transition does not
  receive it.
- Watching or unwatching itself does not create a notification.
- `create_ticket` does not notify (a new ticket has no watchers yet).

---

## Hidden Tests Check For

- A watcher receives `"<ticket_id>:<new_status>"` for each successful transition
  of a watched ticket, in chronological order (e.g. `in_progress`, `resolved`,
  `closed`, `open` across a full cycle).
- Multiple watchers of the same ticket each receive the notification.
- An agent watching several tickets sees all of their notifications interleaved in
  the global order the transitions happened.
- Rejected transitions produce no notification.
- Unwatching stops future notifications but keeps already-received ones; watching
  late does not back-fill missed transitions.
- `watch` returns `False` for an unknown ticket or a duplicate subscription;
  `unwatch` returns `False` for an unknown ticket or a non-subscriber.
- `notifications` for an agent who received none is `[]`.
- A `reopen` notification is delivered even though it also clears the assignee.
