# Factory Data Platform

A portfolio project that presents maintenance, budget and transaction review information for a Brazilian food manufacturer's anonymized data.

## Language

**Alert** (pt: Alerta):
A transaction whose amount deviates more than 20% from its cost center's running mean at detection.
_Avoid_: Flagged alert, transaction alert

**Pending** (pt: Pendente):
The state of an Alert nobody has reviewed yet.
_Avoid_: Unreviewed, flagged

**Reviewed** (pt: Revisado):
The state of an Alert someone has marked as Legitimate or Confirmed anomaly.

**Legitimate** (pt: Legítimo):
The outcome of a Reviewed Alert whose transaction the reviewer found acceptable.

**Confirmed anomaly** (pt: Anomalia confirmada):
The outcome of a Reviewed Alert whose transaction the reviewer found genuinely irregular.
_Avoid_: Anomaly (alone), flagged

**Reference date** (pt: Data de referência):
The date maintenance status is measured from: the date of the most recent maintenance record.
_Avoid_: Today, current date

**Overdue** (pt: Atrasada):
The maintenance status of a machine whose next due date is before the Reference date.

**Due soon** (pt: Vence em breve):
The maintenance status of a machine whose next due date is within 7 days after the Reference date.
