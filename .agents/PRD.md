# BagiTHR — Product Requirements Document

## Overview

BagiTHR is a realtime social finance platform built on Stellar blockchain that modernizes THR (Tunjangan Hari Raya) distribution through interactive community-driven experiences.

The platform combines:
- direct digital THR transfer,
- realtime giveaway rooms,
- competitive claim systems,
- creator engagement,
- and blockchain-based payment infrastructure.

The goal is to transform traditional THR distribution into a viral, social, and realtime digital experience.

---

# Product Vision

Build a consumer-friendly Web3 social payment platform that feels:
- fun,
- realtime,
- accessible,
- mobile-first,
- and easy for non-crypto users.

BagiTHR should avoid:
- complicated crypto UX,
- wallet-address-heavy interaction,
- corporate SaaS appearance,
- and technical onboarding friction.

The platform should feel closer to:
- livestream interaction,
- flash sale excitement,
- and social community engagement.

---

# Core Product Goals

## Primary Goals

### 1. Simplify Digital THR Distribution
Allow users to distribute THR quickly using usernames instead of wallet addresses.

### 2. Create Realtime Social Interaction
Build competitive claim experiences through countdown-based THR rooms.

### 3. Reduce Blockchain Complexity
Make blockchain interaction invisible for mainstream users.

### 4. Demonstrate Real Consumer Blockchain Utility
Show practical usage of Stellar infrastructure for realtime payments and asset distribution.

---

# Core User Experience Principles

## UX Direction

The platform should feel:
- lightweight,
- responsive,
- energetic,
- realtime,
- and socially interactive.

Important UX characteristics:
- countdown tension,
- realtime updates,
- instant feedback,
- smooth animations,
- mobile-first interaction,
- and low-friction onboarding.

Avoid:
- static dashboard feeling,
- enterprise SaaS appearance,
- cluttered crypto UI,
- excessive forms,
- and overtechnical blockchain terminology.

---

# Target Users

## Primary Users
- Family users distributing THR
- Content creators
- Web3 communities

## Secondary Users
- Event organizers
- Crypto-curious users
- Online communities

---

# Core Features

# 1. Direct THR Transfer

Users can send THR directly using usernames instead of wallet addresses.

## Requirements
- Username-based transfer
- Instant transfer feedback
- Transaction success state
- Realtime notification
- Mobile-friendly flow

## UX Notes
Transfer flow should feel simple and fast like a modern social payment app.

---

# 2. THR Room System

Users can create realtime THR giveaway rooms.

## Room Configuration
- Total reward pool
- Maximum participants
- Winner slots
- Distribution rules
- Claim start time

## Room Experience
Participants enter a waiting room before claim session begins.

The room should emphasize:
- anticipation,
- participant activity,
- countdown tension,
- and realtime synchronization.

---

# 3. Waiting Room System

Participants join before claim session starts.

## Waiting Room Features
- Countdown timer
- Participant counter
- Room status
- Join queue
- Live updates

## UX Notes
The waiting room is a core engagement mechanic.

It should feel:
- alive,
- realtime,
- and event-driven.

---

# 4. Realtime Claim System

Participants claim rewards simultaneously once countdown ends.

## Requirements
- Queue-based validation
- Winner slot locking
- Duplicate prevention
- Realtime winner updates
- Fast claim processing

## Technical Direction
System must support concurrent realtime requests fairly.

---

# 5. Social Sharing System

Users can generate shareable social banners after receiving rewards.

## Banner Content
- Username
- Reward amount
- Creator/sender name
- Timestamp

## Supported Platforms
- Instagram
- Threads
- Twitter/X
- WhatsApp

## UX Goal
Encourage viral social sharing and organic growth.

---

# 6. XLM to USDC Swap

Users can convert received XLM into USDC inside the application.

## Requirements
- Live exchange rate
- Fast swap execution
- Transaction feedback
- Balance update

## UX Goal
Reduce crypto volatility exposure for mainstream users.

---

# Realtime System Requirements

The application heavily depends on realtime interaction.

## Realtime Features
- Countdown synchronization
- Participant updates
- Claim activity
- Winner announcements
- Room state synchronization

## Performance Targets
- Claim response < 3 seconds
- Transaction completion < 3 seconds
- High concurrent participant support

---

# Design Philosophy

## Visual Direction

The UI should feel:
- modern,
- immersive,
- elegant,
- dark-theme-first,
- and social-focused.

Avoid:
- excessive glassmorphism,
- crypto casino aesthetics,
- overwhelming gradients,
- and cluttered dashboards.

## UI Priorities
- readability,
- responsive layouts,
- consistent spacing,
- smooth motion,
- and clear interaction states.

---

# Frontend Architecture Goals

Frontend architecture should prioritize:
- scalability,
- reusable component systems,
- realtime state synchronization,
- AI-assisted development friendliness,
- and maintainable design systems.

## Frontend Stack
- Next.js
- TypeScript
- TailwindCSS
- shadcn/ui
- Zustand
- Framer Motion

---

# AI Development Rules

The project is developed using AI-assisted workflow.

All generated code should:
- follow semantic design tokens,
- use reusable UI components,
- avoid hardcoded styles,
- follow feature-based architecture,
- and prioritize readability.

Avoid:
- monolithic components,
- duplicated Tailwind classes,
- inline styling,
- and unnecessary abstraction.

---

# Mobile Experience

The platform is primarily mobile-first.

All interfaces should:
- work smoothly on mobile devices,
- support responsive layouts,
- maintain realtime responsiveness,
- and prioritize touch interaction.

---

# Success Metrics

## Product Metrics
- Successful THR transactions
- THR room creation count
- Repeat participation rate
- Social share rate
- User onboarding completion

## Technical Metrics
- Low latency realtime synchronization
- Stable websocket connection
- Fast claim processing
- Reliable transaction execution
- High uptime

---

# Long-Term Expansion

Potential future expansion:
- creator tipping,
- community rewards,
- livestream interaction,
- event distribution systems,
- and broader social finance features.

---

# Engineering Notes

This project prioritizes:
- frontend experience quality,
- realtime interaction quality,
- scalable architecture,
- and maintainable AI-native development workflow.

Blockchain integration should support UX,
not dominate UX.