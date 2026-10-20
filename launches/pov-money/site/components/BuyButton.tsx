'use client'

import { useState } from 'react'
import { Arrow } from '@/components/Chrome'

/** Edson's Stripe payment link (supplied 2026-10-20). NEXT_PUBLIC_CHECKOUT_URL overrides it. */
const STRIPE_CHECKOUT_URL = 'https://buy.stripe.com/8x214pcx7cLPbcng8W9MY00'

/**
 * The only buy action on the site. Links to the Stripe checkout (NEXT_PUBLIC_CHECKOUT_URL, else the
 * default above). If both are ever empty, it falls back to an honest preview: clicking explains that
 * checkout is not connected and no payment can be taken.
 */
export function BuyButton({ label = 'Buy Now', className = 'pill-lime', id }: { label?: string; className?: string; id?: string }) {
  const checkout = process.env.NEXT_PUBLIC_CHECKOUT_URL || STRIPE_CHECKOUT_URL
  const [open, setOpen] = useState(false)

  if (checkout) {
    return (
      <a href={checkout} className={className} id={id}>
        {label} <Arrow />
      </a>
    )
  }

  return (
    <div className="flex flex-col items-start gap-3">
      <button
        type="button"
        className={className}
        id={id}
        aria-expanded={open}
        aria-controls={id ? `${id}-note` : undefined}
        onClick={() => setOpen((v) => !v)}
      >
        {label} <Arrow />
      </button>
      {open ? (
        <p
          id={id ? `${id}-note` : undefined}
          className="max-w-md rounded-[16px] border-[1.5px] border-dashed border-ink bg-white px-4 py-3 text-[15px] leading-relaxed"
          role="status"
        >
          Preview: checkout is not connected yet, so no payment can be taken on this page. The seller adds the payment link
          before launch.
        </p>
      ) : null}
    </div>
  )
}
