import FaqList from '../../components/FaqList'

export default function Faq() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
      <h1 className="text-3xl font-bold">Frequently asked questions</h1>
      <p className="mt-2 text-muted">Everything you need to know about renting with Rentify.</p>
      <div className="mt-8">
        <FaqList />
      </div>
    </div>
  )
}
