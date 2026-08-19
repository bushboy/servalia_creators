# IngramSpark submission checklist

Book: {{ book.final_title or book.working_title }}
Edition: {{ edition.format }}
ISBN: {{ edition.isbn or "(not set)" }}
Proof review: {{ edition.proof_review_status }}

- [ ] ISBN is present for print editions.
- [ ] Format, trim, and language match the interior file plan.
- [ ] List price and currency are set.
- [ ] Proof-review status is recorded (this is a status, not a live Ingram API).
- [ ] Description is author-approved.

This package prepares an IngramSpark upload. It does not publish on the author’s behalf.
