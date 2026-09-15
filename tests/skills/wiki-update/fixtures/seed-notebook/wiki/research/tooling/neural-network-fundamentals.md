---
title: "Neural network fundamentals"
date: 2026-01-14
source_url: "internal://skilltest/seed/neural-network-fundamentals"
ingested_by: skilltest-fixture
tier: self
confidence: medium
last_reviewed: 2026-01-14
review_after: 2026-04-14
tags: [neural-networks, deep-learning, training]
---

# Neural network fundamentals

## TL;DR

A neural network is layers of simple units, each computing a weighted sum of its inputs and passing it through a non-linear function. Training adjusts the weights to reduce the error on examples, using gradients computed by backpropagation.

## Parts

- **Layers**: an input layer, hidden layers, an output layer.
- **Weights and biases**: the numbers training changes.
- **Activation functions**: the non-linearity that lets stacked layers represent more than a straight line.

## Training

A loss function measures how wrong the outputs are; gradient descent nudges every weight in the direction that lowers the loss, and backpropagation computes those directions efficiently, layer by layer from the output back.

## Related in this wiki

- [Transformer attention overview](../long-term/transformer-attention-overview.md): the architecture language models build from these parts.
- [Context engineering basics](../best-practices/context-engineering-basics.md): what a trained model is given to work with at run time.
