import { Github, Mail, FileText, GraduationCap, Linkedin } from 'lucide-react';

export const personalInfo = {
  name: "Sam Belliveau",
  title: "Undergraduate Researcher @ Cornell University",
  tagline: "Democratizing complex data capture workflows through end-to-end systems.",
  bio: "I am a researcher interested in systems, compilers, and programming languages, driven by the trade-offs between manual memory management (RAII) and modern garbage collection (ZGC/G1). My work focuses on how system architecture impacts software reliability, bridging the gap between high-level abstractions and bare-metal performance. I specialize in optimizing the hardware-software interface, from RISC-V/ARM Cortex-M constraints to efficient DMA buffering, while leveraging tools like Bash for automation and C/C++ for performance-critical loops.",
  email: "srb343@cornell.edu",
  links: [
    { name: "Github", url: "https://github.com/Sam-Belliveau", icon: Github },
    { name: "Google Scholar", url: "#", icon: GraduationCap },
    { name: "Email", url: "mailto:srb343@cornell.edu", icon: Mail },
    { name: "CV", url: "/src/assets/resume_repo/Sam-Belliveau-Robotics.pdf", icon: FileText },
    { name: "LinkedIn", url: "https://www.linkedin.com/in/sam-belliveau", icon: Linkedin },
  ]
};

export const researchProjects = [
  {
    title: "CaptureGraph",
    role: "Lead Researcher, First Author",
    status: "In Prep",
    summary: "Conducting reproducible research in computational photography is often hindered by tightly coupled capture logic and application code. I designed CaptureGraph, a system that decouples capture procedures from application logic using a custom Python-based DSL. This architecture enables \"Distribution-Aware\" data collection, ensuring data is organized into semantic hierarchies ready for algorithmic analysis immediately upon capture.",
    tech: ["Python", "iOS (Swift/SwiftUI)", "JSON Serialization"],
    image: null // Placeholder
  },
  {
    title: "CineCraft",
    role: "Researcher, Second Author",
    status: "Under Review",
    summary: "Achieving professional \"focus pulling\" on consumer hardware is difficult due to the lack of precise control. I developed CineCraft, a tool for \"Cellular Cinematography\" that utilizes a \"Two-Plane Model\" to abstract the 3D scene. The system automates focus and zoom operations using computer vision, effectively acting as a virtual \"focus puller\" to democratize complex cinematographic techniques.",
    tech: ["iOS (Swift, Metal)", "Vision Framework", "Computer Vision"],
    image: null // Placeholder
  },
  {
    title: "DynaBox",
    role: "Researcher, Co-Author",
    status: "In Prep",
    summary: "Digitizing analog \"talkbox\" performances involves capturing the nuanced resonance of the human vocal tract. I co-developed DynaBox, a system that uses a smartphone to capture these performances, implementing AutoRegressive with eXtra input (ARX) models to isolate vocal tract resonances. The system serializes extracted formants into MIDI messages, allowing analog performances to be edited in DAWs.",
    tech: ["Audio Signal Processing", "Python", "MIDI Protocol"],
    image: null // Placeholder
  }
];

export const engineeringProjects = [
  {
    title: "Real-Time Sound Localization",
    summary: "I architected an embedded system on a Raspberry Pi Pico to achieve high-accuracy directional hearing on a $20 BOM. Using C/C++ and direct DMA buffering to bypass CPU overhead, I implemented a custom \"ping-pong\" strategy to sample three microphones at 50kHz. The system achieved zero-latency sampling and precise sound localization through optimized cross-correlation algorithms.",
    tech: ["C/C++", "DMA Buffering", "Cross-Correlation"],
  }
];

export const teachingExperience = [
  {
    course: "ECE 4760 (Digital Systems Design)",
    role: "Teaching Assistant",
    institution: "Cornell University",
    description: "I mentored students in \"Digital Systems Design,\" breaking down complex technical concepts like hardware debugging and microcontroller pin configurations. I focused on helping students understand the theoretical underpinnings while mastering the practical challenges of embedded development."
  },
  {
    course: "ECE 3250 (Signal Processing)",
    role: "Teaching Assistant",
    institution: "Cornell University",
    description: "I conducted office hours for \"Signal Processing,\" explaining concepts like Fourier transforms. I emphasized the communication of complex mathematical ideas to help students grasp the material."
  }
];

export const industryExperience = [
  {
    company: "Reddit",
    role: "Software Engineer Intern",
    team: "Consumer Product Team",
    description: "I developed automated scripts (using Python and Bash) to generate large-scale, realistic test data sets. This automation was critical for training and validating safety classification models, ensuring they could robustly handle diverse and edge-case user content. My work directly contributed to improving the reliability of content moderation systems."
  }
];
