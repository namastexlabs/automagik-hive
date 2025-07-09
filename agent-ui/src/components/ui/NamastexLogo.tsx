'use client'

import React from 'react'
import Image from 'next/image'

interface NamastexLogoProps {
  className?: string
  size?: 'xs' | 'sm' | 'md' | 'lg'
}

const sizeMap = {
  xs: 32,
  sm: 48, 
  md: 64,
  lg: 80
}

export const NamastexLogo: React.FC<NamastexLogoProps> = ({ 
  className = '', 
  size = 'md' 
}) => {
  const sizeValue = sizeMap[size]
  
  return (
    <Image
      src="/nmstx.svg"
      alt="Namastex Logo"
      width={sizeValue}
      height={sizeValue}
      className={className}
    />
  )
}