/**
 * @file UploadedImage.tsx
 * @description Simple TypeScript React component to render images placed in the public/uploads folder.
 *              Use the `filename` prop (e.g. "hero.jpg") and the component will render /uploads/{filename}.
 */

import React, { useState } from 'react'

/**
 * Props for UploadedImage component.
 */
export interface UploadedImageProps {
  /** Filename relative to /uploads (e.g. "hero.jpg") */
  filename: string
  /** Image alt text */
  alt?: string
  /** Optional additional Tailwind/CSS classes */
  className?: string
  /** Optional inline style */
  style?: React.CSSProperties
}

/**
 * UploadedImage
 * Renders an <img> that points at /uploads/{filename}. If the image fails to load
 * a small fallback element is shown instead.
 *
 * Example:
 * <UploadedImage filename="hero-malaysia.jpg" alt="Malaysia hero" className="w-full h-64 object-cover" />
 *
 * @param props UploadedImageProps
 */
export function UploadedImage({
  filename,
  alt = '',
  className = '',
  style,
}: UploadedImageProps) {
  const [errored, setErrored] = useState(false)

  // If no filename provided, render nothing.
  if (!filename) return null

  const src = `/uploads/${filename}`

  // Show a subtle fallback if the image could not be loaded.
  if (errored) {
    return (
      <div
        className={`flex items-center justify-center rounded-md bg-emerald-50 text-emerald-700 ${className}`}
        style={style}
        role="img"
        aria-label={`Missing image ${filename}`}
      >
        <span className="text-sm">Image not found</span>
      </div>
    )
  }

  return (
    <img
      src={src}
      alt={alt || filename}
      className={className}
      style={style}
      onError={() => setErrored(true)}
    />
  )
}
