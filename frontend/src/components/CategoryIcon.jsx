import { Camera, Drone, Gamepad2, Guitar, Laptop, Mic, Package, Projector } from 'lucide-react'

const ICONS = {
  cameras: Camera,
  'gaming-consoles': Gamepad2,
  laptops: Laptop,
  drones: Drone,
  'musical-instruments': Guitar,
  'audio-equipment': Mic,
  projectors: Projector,
}

export default function CategoryIcon({ slug, className = 'h-6 w-6' }) {
  const Icon = ICONS[slug] ?? Package
  return <Icon className={className} aria-hidden="true" />
}
