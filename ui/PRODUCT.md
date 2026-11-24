# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

The primary viewer is a general tech visitor: a developer or recruiter who opens a portfolio link and may not know SLAM, lidar or ROS. They need the screen to explain itself while they watch. Robotics reviewers also visit, and the detail they look for should stay reachable.

## Product Purpose

Gridbot is a simulated warehouse robot that explores, maps, localizes and navigates. The browser draws each layer of its thinking live. After 30 seconds, a visitor should be able to say: "I can see what the robot senses and believes, and where that differs from reality."

## Positioning

Everything on screen comes from real algorithm state, produced by hand-written robotics algorithms running on a server. Visuals are never faked or tweened to look better than the algorithm is doing.

## Operating Context

One shared robot runs on the server and cycles through a playlist of runs, so everyone watching sees the same robot. Visitors arrive from a shared link, on desktop first. Phones get a simplified view that is still worth watching.

## Capabilities and Constraints

- Visitors can only watch. They cannot set goals, add obstacles, change the run or affect the simulation.
- Phase 1 shows the map, the robot and its lidar while the robot follows a scripted drive from the scenario. Mapping, particles, planning and SLAM arrive in later phases, so the layout has to leave room for them.
- The UI receives JSON from the gateway at a 20 Hz simulation rate and uses the same format for both runtimes.
- The UI is TypeScript with Vite.
- Gridbot stays independent of Phoenix Firefly and its design system.

## Brand Commitments

"Gridbot" is a working name. The project spec names Tesla's FSD debug view, in 2D, as the reference for the idea of showing a machine's perception live.
The owner chose the engineering-console direction on 2026-11-18: a robotics data viewer in the Foxglove tradition, finished to the standard of polished developer tools such as Linear and Vercel. Treat that familiar form as the commitment, not as a starting point to restyle.

## Evidence on Hand

No screenshots, recordings, metrics or live data exist yet. Prototype data must be labeled as simulated until the runner produces real runs.

## Product Principles

- Show the robot's belief beside the truth whenever both exist.
- Explain with the picture first, and with words only where the picture needs help.
- Draw only what the algorithms produced.
- Give each later phase a place to appear without rebuilding the screen.
