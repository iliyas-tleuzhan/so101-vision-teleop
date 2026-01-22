# SO101 Vision-Assisted Teleoperation
## **Vision-assisted hand-tracking teleoperation for the LeRobot SO101 robotic arm**

### This project implements a **real-time, vision-assisted teleoperation system** for a 6-DOF LeRobot SO101 robotic arm using:
1) Laptop-side computer vision (MediaPipe Hands)
2) Network-based command streaming
3) Raspberry Pi 5 as a safety-critical robot controller
4) Dynamixel-style smart servos on a TTL serial bus

### This system is **not autonomous**.  
All robot motion is directly driven by a human operator’s hand movement and is continuously supervised by safety constraints on the Raspberry Pi.

### The project is designed as a **portfolio-quality robotics system** demonstrating computer vision, embedded control, networking, and safety-aware software architecture.

## Project goals
The primary goal of this project is to build a **robust, safe, and understandable teleoperation system** suitable for a robotics and computer engineering portfolio.

This project aims to demonstrate:
1) End-to-end hardware–software integration  
2) Real-time computer vision applied to robotics  
3) Networked control of physical systems  
4) Safety-first embedded system design  
5) Structured logging and reproducibility  

---

## Design principles
The system is intentionally designed around the following principles:

1) **Safety before performance**  
   - All safety decisions are enforced on the Raspberry Pi  
   - The laptop is never trusted to directly control hardware  

2) **Simplicity over complexity (v1)**  
   - No inverse kinematics  
   - No autonomous behavior  
   - Feature-based control instead of full pose estimation  

3) **Clear separation of responsibilities**  
   - Laptop: perception, intent generation  
   - Raspberry Pi: validation, safety, actuation  

4) **Modularity and readability**  
   - Small, focused modules  
   - Configuration-driven behavior  
   - Code intended to be read and modified  

5) **Reproducibility**  
   - Every session can be logged  
   - Logged motion can be replayed deterministically  
