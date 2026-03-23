import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders correctly', () => {
    render(<App />)
    // 根据实际输出，页面包含 "Get started" 字样
    expect(screen.getByText(/Get started/i)).toBeInTheDocument()
  })
})
