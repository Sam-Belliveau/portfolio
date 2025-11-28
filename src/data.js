import { Github, Mail, FileText, GraduationCap, Linkedin } from 'lucide-react';

export const personalInfo = {
  name: "Sam Belliveau",
  title: "Undergraduate Researcher @ Cornell University",
  tagline: "Democratizing complex data capture workflows through end-to-end systems.",
  bio: "My research interests lie at the intersection of Human-Computer Interaction (HCI), Computational Photography, and Systems Engineering. I am driven by the desire to bridge the gap between creative intent and rigid capture tools by architecting systems that span hardware, low-level software, and user interfaces.",
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
    description: "A system designed to decouple capture procedures from application logic. It features a Python-based Domain Specific Language (DSL) allowing researchers to programmatically define complex capture workflows, serialized into JSON for execution on a companion iOS app.",
    tech: ["Python", "iOS (Swift/SwiftUI)", "JSON Serialization"],
    insight: "Enables \"Distribution-Aware\" data collection, organizing data into semantic hierarchies ready for algorithmic analysis.",
    image: null // Placeholder
  },
  {
    title: "CineCraft",
    role: "Researcher, Second Author",
    status: "Under Review",
    description: "A tool for \"Cellular Cinematography\" that unifies shot planning and execution. Utilizes a \"Shot Plan\" data structure based on a Two-Plane Model (Foreground/Background) to define relative camera motion.",
    tech: ["iOS (Swift, Metal)", "Vision Framework", "Computer Vision"],
    insight: "Automates focus and zoom in real-time, effectively acting as a virtual \"focus puller\" to democratize complex shots like dolly zooms.",
    image: null // Placeholder
  },
  {
    title: "DynaBox",
    role: "Researcher, Co-Author",
    status: "In Prep",
    description: "A system to digitize analog \"talkbox\" performances using a smartphone. Implements AutoRegressive with eXtra input (ARX) models to isolate vocal tract resonances.",
    tech: ["Audio Signal Processing", "Python", "MIDI Protocol"],
    insight: "Serializes formants into MIDI Continuous Controller (CC) messages, allowing analog performances to be edited in DAWs like Logic Pro.",
    image: null // Placeholder
  }
];

export const engineeringProjects = [
  {
    title: "Real-Time Sound Localization",
    description: "An embedded system architected on a Raspberry Pi Pico to achieve high-accuracy directional hearing on constrained hardware ($20 BOM).",
    tech: ["C/C++", "DMA Buffering", "Cross-Correlation"],
    highlight: "Implemented a custom \"ping-pong\" DMA strategy to sample three microphones at 50kHz with zero latency."
  }
];

export const teachingExperience = [
  {
    course: "ECE 4760 (Digital Systems Design)",
    role: "Teaching Assistant",
    institution: "Cornell University",
    description: "Assisting students with hardware debugging and documenting pin configurations."
  },
  {
    course: "ECE 3250 (Signal Processing)",
    role: "Teaching Assistant",
    institution: "Cornell University",
    description: "Conducting office hours for concepts like Fourier transforms."
  }
];

export const industryExperience = [
  {
    company: "Reddit",
    role: "Software Engineer Intern",
    team: "Consumer Product Team",
    description: "Developed scripts to create realistic test data for safety classification models."
  }
];
