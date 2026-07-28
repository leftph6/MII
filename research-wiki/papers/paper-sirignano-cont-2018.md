---
id: paper-sirignano-cont-2018
type: paper
title: Universal Features of Price Formation
status: verified
tags:
- CLOB
- cross-asset
- market-microstructure
created_at: '2026-07-27T17:33:27Z'
updated_at: '2026-07-27T17:33:27Z'
source_url: https://arxiv.org/abs/1803.06917
access_date: '2026-07-28'
---

## Evidence

Sirignano and Cont study universal deep representations for price formation across instruments using limit-order-book data. The reusable lesson is cross-asset pooling with a time-aware encoder; the original CLOB input is not a drop-in representation for a BSC CFMM.

## Relevance

Supports shared encoders across pools/tokens after replacing bid/ask levels with reserves, event flow, impact and block-position features.

## Limitation

The paper does not identify on-chain roles or latent intent and does not validate PancakeSwap-style AMMs.

## Source

https://arxiv.org/abs/1803.06917
