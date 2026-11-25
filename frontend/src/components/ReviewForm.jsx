import { useState } from 'react'
import { errorMessage } from '../utils/format'
import Button from './Button'
import { Alert } from './Feedback'
import Input from './Input'
import StarRating from './StarRating'

/** Rating + comment form used to write or edit a review. `onSubmit` receives { rating, comment }. */
export default function ReviewForm({ initialRating = 0, initialComment = '', submitLabel, onSubmit, onCancel }) {
  const [rating, setRating] = useState(initialRating)
  const [comment, setComment] = useState(initialComment)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    if (rating < 1) {
      setError('Choose a star rating.')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      await onSubmit({ rating, comment: comment.trim() || null })
    } catch (err) {
      setError(errorMessage(err))
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      {error && <Alert>{error}</Alert>}
      <div>
        <p className="mb-1 text-sm font-medium">Your rating</p>
        <StarRating value={rating} onChange={setRating} size="h-7 w-7" />
      </div>
      <Input
        as="textarea"
        rows={4}
        label="Your review (optional)"
        maxLength={2000}
        value={comment}
        onChange={(event) => setComment(event.target.value)}
      />
      <div className="flex justify-end gap-2">
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel} disabled={submitting}>
            Cancel
          </Button>
        )}
        <Button type="submit" loading={submitting}>
          {submitLabel}
        </Button>
      </div>
    </form>
  )
}
