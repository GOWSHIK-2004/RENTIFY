import { useState } from 'react'
import { errorMessage } from '../utils/format'
import Button from './Button'
import { Alert } from './Feedback'
import Input from './Input'
import Modal from './Modal'

/**
 * Asks "are you sure?" and runs `onConfirm` (async). Shows the error if it fails and
 * stays open. With `askReason`, a free-text reason is passed to onConfirm.
 */
export default function ConfirmModal({
  title,
  message,
  confirmLabel = 'Confirm',
  danger = false,
  askReason = false,
  onConfirm,
  onClose,
}) {
  const [reason, setReason] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const submit = async () => {
    setSubmitting(true)
    setError('')
    try {
      await onConfirm(reason.trim() || undefined)
      onClose()
    } catch (err) {
      setError(errorMessage(err))
      setSubmitting(false)
    }
  }

  return (
    <Modal title={title} onClose={submitting ? () => {} : onClose}>
      <div className="space-y-4">
        {error && <Alert>{error}</Alert>}
        <p className="text-sm text-muted">{message}</p>
        {askReason && (
          <Input
            as="textarea"
            rows={3}
            label="Reason (optional)"
            maxLength={500}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
        )}
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose} disabled={submitting}>
            Keep it
          </Button>
          <Button variant={danger ? 'danger' : 'primary'} onClick={submit} loading={submitting}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </Modal>
  )
}
