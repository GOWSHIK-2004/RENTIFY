import { ChevronDown } from 'lucide-react'

export const FAQS = [
  {
    question: 'How does renting work?',
    answer:
      'Pick equipment, choose pickup and return dates, check availability and confirm your booking. You are charged the daily price for each rental day; the return day is not charged.',
  },
  {
    question: 'How long can I rent equipment?',
    answer: 'From 1 to 30 days per booking. The pickup date cannot be in the past.',
  },
  {
    question: 'Is my payment real?',
    answer:
      'No. Rentify is a demonstration project. Checkout is simulated, no card details are collected and no money moves.',
  },
  {
    question: 'Can I cancel a booking?',
    answer:
      'Yes. You can cancel a confirmed booking any time before its pickup date. The simulated payment is refunded automatically.',
  },
  {
    question: 'What happens if equipment is returned late?',
    answer:
      'Late equipment is flagged as overdue for our team, and that unit is not offered to new customers until it is back.',
  },
  {
    question: 'Who owns the equipment?',
    answer: 'Rentify owns and maintains all rental inventory. It is not a marketplace of third-party sellers.',
  },
]

export default function FaqList() {
  return (
    <div className="divide-y divide-line rounded-xl border border-line bg-white">
      {FAQS.map((item) => (
        <details key={item.question} className="group px-5 py-4">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-medium">
            {item.question}
            <ChevronDown className="h-4 w-4 shrink-0 text-muted transition-transform group-open:rotate-180" aria-hidden="true" />
          </summary>
          <p className="mt-2 text-sm text-muted">{item.answer}</p>
        </details>
      ))}
    </div>
  )
}
