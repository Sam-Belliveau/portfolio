import {FileText, Github, Linkedin, Mail} from 'lucide-react';

export const personalInfo = {
  name: 'Sam Belliveau',
  title: 'Undergraduate Researcher @ Cornell University',
  bio:
      'I am an undergraduate researcher at Cornell University under Abe Davis. My research interests lie at the intersection of Human Computer Interaction (HCI), Computational Photography, and Signal Processing.',
  links: [
    {name: 'Github', url: 'https://github.com/Sam-Belliveau', icon: Github},
    {
      name: 'LinkedIn',
      url: 'https://www.linkedin.com/in/sam-belliveau',
      icon: Linkedin
    },
    {name: 'Email', url: 'mailto:srb343@cornell.edu', icon: Mail},
  ]
};

export const researchProjects = [
  {
    title: 'CaptureGraph',
    role: 'Sam Belliveau, Abe Davis',
    status: 'Under Review (SIGGRAPH 2026)',
    summary:
        'Hard-coding specific capture modes is unsustainable for diverse scientific needs. I architected CaptureGraph, an end-to-end system that decouples capture procedures from application logic using a custom Python-based DSL. This "Distribution-Aware" system serializes procedures into JSON for a companion iOS app, providing real-time, step-by-step guidance.',
    tech: [
      'Python (DSL)', 'iOS (Swift/SwiftUI)', 'JSON Serialization', 'Mobile HCI'
    ],
    documents: [
      {
        name: 'Presentation',
        url:
            'https://docs.google.com/presentation/d/11Wu5D2UKaE0_5eCtvr8rnnWVYde__XgE/edit?usp=sharing&ouid=109247465115682025485&rtpof=true&sd=true'
      },
    ],
    image: null
  },
  {
    title: 'CineCraft',
    role: 'Nhan Tran, Sam Belliveau, Abe Davis',
    status: 'Accepted to CHI2026',
    summary:
        'Complex shots like synchronized dolly zooms traditionally require a coordinated film crew. I helped develop CineCraft, a tool for "Cellular Cinematography" that unifies planning, capture, and post-processing via a "Shot Plan" data structure. Utilizing a "Two-Plane Model" (Foreground/Background), the system automates focus and zoom in real-time. User studies demonstrated it significantly outperformed standard camera apps in execution success and matching creative intent.',
    tech: [
      'iOS (Swift, Metal)', 'Vision Framework', 'Computer Vision',
      'Video Stabilization'
    ],
    documents: [],
    image: null
  },
  {
    title: 'DynaBox',
    role: 'Jason Klein, Sam Belliveau',
    status: 'In Prep',
    summary:
        'Digitizing analog "talkbox" performances requires capturing the nuanced resonance of the vocal tract. I co-developed DynaBox, implementing AutoRegressive with eXtra input (ARX) models to isolate vocal tract resonances (formants) from source audio using only a smartphone. I engineered a pipeline to serialize these formants into MIDI Continuous Controller (CC) messages, allowing analog performances to be used as digital instruments in DAWs like Logic Pro.',
    tech: ['Audio Signal Processing (ARX)', 'Python', 'MIDI Protocol', 'iOS'],
    documents: [],
    image: null
  }
];

export const engineeringProjects = [
  {
    title: 'Real-Time Sound Localization (LINK)',
    link: 'https://sam-belliveau.github.io/ece-4760-final-project/index.html',
    role: 'System Architect',
    summary:
        'I architected a sound localization system on a Raspberry Pi Pico to achieve high-accuracy directional hearing with a sub-$20 BOM. I implemented a custom "ping-pong" DMA buffer strategy and cross-correlation engine in C to sample three synchronized MEMS microphones at 50kHz with zero latency. The system visualizes the sound source\'s location probability via a real-time heatmap on a VGA display.',
    tech: [
      'C', 'Raspberry Pi Pico (RP2040)', 'DMA Buffering', 'Signal Processing'
    ],
  },
  {
    title: 'Cornell Autonomous Underwater Vehicles',
    role: 'Software Team Member',
    summary:
        'I optimized the control systems for an autonomous submarine. I reduced CPU usage by 80% by implementing Kalman Filtering using Nvidia’s CUDA framework for linear algebra computations and improved movement precision by implementing least squares optimization for thruster speed determination.',
    tech: ['Numpy', 'CUDA', 'Kalman Filtering', 'Optimization'],
  }
];

export const teachingExperience = [
  {
    course: 'ECE 4760 (Introduction to Microcontrollers)',
    role: 'Teaching Assistant',
    institution: 'Cornell University',
    description:
        'I assist students with hardware and software debugging as they work on projects using the Raspberry Pi Pico. I help improve project instructions to better avoid common pitfalls students face.'
  },
  {
    course: 'ECE 3250 (Signals & Systems)',
    role: 'Teaching Assistant',
    institution: 'Cornell University',
    description:
        'I conduct office hours to help students master signal processing concepts, including the Fourier transform and convolutions.'
  },
  {
    course: 'VEX Robotics',
    role: 'Coach',
    institution: 'PLAYIDEAS Inc.',
    description:
        'I developed and taught lesson plans on PID control and Odometry, translating complex control theory concepts into accessible lessons for students.'
  }
];

export const industryExperience = [{
  company: 'Reddit',
  role: 'Software Engineering Intern',
  team: 'Consumer Product Team',
  description:
      'I worked with the Taxonomy Group to classify safety for 138,000+ subreddits. I developed automated scripts to generate realistic test data for safety classification models and built statistical dashboards to flag problematic content, directly improving the reliability of content moderation.'
}];
