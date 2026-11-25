import Button from '../../components/Button'

export default function About() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
      <h1 className="text-3xl font-bold">About Rentify</h1>
      <p className="mt-2 text-lg text-primary">Rent More. Own Less.</p>
      <div className="mt-6 space-y-4 text-muted">
        <p>
          Rentify makes expensive equipment accessible. Instead of buying a camera for one trip or a projector for one
          event, rent it by the day and give it back when you are done.
        </p>
        <p>
          We own and maintain every item in our inventory, so there are no third-party sellers: just well-kept gear and
          clear daily prices. Availability is checked against real bookings, so what you see is what you get.
        </p>
      </div>
      <div className="mt-8 rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
        <h2 className="font-semibold">This is a demonstration project</h2>
        <p className="mt-1">
          Rentify was built to practise full-stack development with React, FastAPI and PostgreSQL. Payments are
          simulated, no card details are collected, and no equipment will be delivered.
        </p>
      </div>
      <Button to="/products" className="mt-8">
        Browse equipment
      </Button>
    </div>
  )
}
