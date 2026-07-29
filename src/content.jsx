import photo from './assets/profile.jpg';
import captureGraphCoverage from './assets/figures/capturegraph-coverage.png';
import cineCraftStoryboard from './assets/figures/cinecraft-storyboard.png';
import dynaboxSpectrograms from './assets/figures/dynabox-spectrograms.png';
import smolVlaSystolicArray from './assets/figures/smolvla-systolic-array.png';
import soundLocalizationBoard from './assets/figures/sound-localization-board.png';
import abeDavisLab from './assets/logos/abe-davis-lab.png';
import cornellSeal from './assets/logos/cornell-seal.png';
import cuauv from './assets/logos/cuauv.png';
import hofstra from './assets/logos/hofstra.png';
import reddit from './assets/logos/reddit.png';

export const profile = {
  name: 'Sam Belliveau',
  citationName: 'S. Belliveau',
  photo,
  headline: 'Ph.D. Student in Computer Science, Cornell University',
  bio: (
    <>
      <p>
        I am an incoming Ph.D. student in Computer Science at Cornell
        University, advised by <a href="https://www.abedavis.com">Abe Davis</a>{' '}
        in the Bowers College of Computing and Information Science. I build
        systems at the intersection of computational photography,
        human&ndash;computer interaction, and signal processing &mdash; tools
        that turn everyday devices into sophisticated instruments for capture
        and measurement.
      </p>
      <p>
        I received my B.S. in Electrical &amp; Computer Engineering from
        Cornell in 2026.
      </p>
    </>
  ),
  links: [
    { label: 'Email', href: 'mailto:sam.belliveau@gmail.com' },
    { label: 'GitHub', href: 'https://github.com/Sam-Belliveau' },
    { label: 'LinkedIn', href: 'https://linkedin.com/in/sam-belliveau' },
    {
      label: 'Résumé',
      href: 'https://github.com/Sam-Belliveau/resume/releases/latest/download/Sam-Belliveau-research.pdf',
    },
  ],
};

export const news = [
  {
    date: 'Aug 2026',
    text: 'Starting my Ph.D. in Computer Science at Cornell, advised by Abe Davis.',
  },
  {
    date: 'May 2026',
    text: 'Graduated from Cornell with a B.S. in Electrical & Computer Engineering.',
  },
  {
    date: 'Jan 2026',
    text: (
      <>
        <em>CineCraft</em> was accepted to CHI 2026.
      </>
    ),
  },
  {
    date: 'June 2025',
    text: (
      <>
        My sound-localization system was{' '}
        <a href="https://hackaday.com/2025/06/27/audio-localization-gear-built-on-the-cheap/">
          featured on Hackaday
        </a>
        .
      </>
    ),
  },
];

export const publications = [
  {
    title: 'CaptureGraph: A Distribution-Aware Programmable Capture Framework',
    authors: ['S. Belliveau', 'A. Davis'],
    venue: 'In preparation',
    note: 'First author — architected a Python DSL and iOS runtime that decouple capture procedures from user guidance, scheduling future captures by the marginal statistical value of each new observation.',
    thumbnail: captureGraphCoverage,
  },
  {
    title: 'CineCraft: Using Shot Plans for Cinematic Capture Guidance',
    authors: ['N. Tran', 'S. Belliveau', 'C. Xu', 'A. Davis'],
    venue: 'CHI 2026',
    note: 'Second author — built the real-time subject-tracking and stabilization loop, resolving tracking–zoom jitter.',
    thumbnail: cineCraftStoryboard,
  },
  {
    title: 'Dynabox: Digitizing Analog Talkbox Performances via ARX Modeling',
    authors: ['J. Klein', 'S. Belliveau', 'A. Davis'],
    venue: 'In preparation',
    note: 'Co-author — implemented ARX models that isolate vocal-tract resonances for MIDI conversion.',
    thumbnail: dynaboxSpectrograms,
  },
];

export const projects = [
  {
    title: 'Real-Time Sound Localization',
    dates: '2025',
    href: 'https://sam-belliveau.github.io/ece-4760-final-project/index.html',
    description:
      'An under-$20 acoustic camera on a Raspberry Pi Pico: three microphones sampled at 50 kHz through a ping-pong DMA scheme, with a comb-filter event detector feeding a cross-correlation engine for time-difference-of-arrival estimation on a live VGA heatmap.',
    tech: ['Embedded C', 'RP2040', 'DMA', 'Signal Processing'],
    thumbnail: soundLocalizationBoard,
  },
  {
    title: 'SmolVLA FPGA Accelerator',
    dates: '2025',
    description:
      'A spatial dataflow architecture on a Xilinx Alveo U280 that accelerates the vision encoder of a vision-language-action model, overlapping QKV projection with attention-score math to reach roughly 20 ms per inference.',
    tech: ['High-Level Synthesis', 'C++', 'Python'],
    thumbnail: smolVlaSystolicArray,
  },
  {
    title: 'Bijective LLM Arithmetic Coder',
    dates: '2026',
    description:
      'An exact-integer arithmetic coder that uses a language model’s next-token distribution as its probability model. Every bit string round-trips exactly, so encrypted payloads decode to fluent cover text under any key.',
    tech: ['Python', 'Information Theory', 'Cryptography'],
  },
  {
    title: 'UCI Chess Engine',
    dates: '2023 — Present',
    href: 'https://github.com/Sam-Belliveau/flying-dutchman',
    description:
      'An alpha-beta engine in Rust extended with opponent modeling: opponent nodes consider only the moves a shallow search says look immediately strong, mimicking human play. Fielded as a Lichess bot.',
    tech: ['Rust', 'Minimax', 'Opponent Modeling'],
  },
  {
    title: 'StuyLib',
    dates: '2020 — 2022',
    href: 'https://github.com/StuyPulse/StuyLib',
    description:
      'An award-winning control-theory and digital-filtering library for FIRST Robotics, now adopted by many other teams.',
    tech: ['Java', 'Control Theory', 'Digital Filtering'],
  },
];

export const experience = [
  {
    organization: 'Cornell University — Abe Davis Lab',
    logo: abeDavisLab,
    role: 'Undergraduate Researcher',
    dates: '2023 — Present',
    summary:
      'Architected CaptureGraph, a programmable capture framework spanning a Python DSL, an iOS runtime, and a team server; reworked 7,000+ lines of legacy Swift to add HDR and RAW capture; built CineCraft’s real-time stabilization loop.',
  },
  {
    organization: 'Cornell University',
    logo: cornellSeal,
    role: 'Teaching Assistant — ECE 4760: Microcontrollers',
    dates: '2025 — 2026',
    summary:
      'Graded weekly labs with detailed feedback on code and reports, and helped lab groups debug their hardware and software during sessions.',
  },
  {
    organization: 'Cornell Autonomous Underwater Vehicles',
    logo: cuauv,
    role: 'Robotics Software Engineer',
    dates: '2023 — 2026',
    summary:
      'Cut CPU usage by 80% by moving Kalman-filter state estimation onto the GPU with CUDA, and improved navigation precision by recasting thruster allocation as a real-time least-squares optimization.',
  },
  {
    organization: 'Reddit, Inc.',
    logo: reddit,
    role: 'Software Intern — Consumer Product Team',
    dates: 'Summers 2021 & 2022',
    summary:
      'Built a moderator-engagement notification system on BigQuery and Cassandra; later joined the Taxonomy Group to classify 138,000+ subreddits and measure classification models against synthetic ground-truth data.',
  },
];

export const education = [
  {
    school: 'Cornell University',
    logo: cornellSeal,
    degree: 'Ph.D. in Computer Science — Bowers CIS, advised by Prof. Abe Davis',
    dates: '2026 — 2031 (expected)',
  },
  {
    school: 'Cornell University',
    logo: cornellSeal,
    degree: 'B.S. in Electrical & Computer Engineering',
    dates: '2023 — 2026',
  },
  {
    school: 'Hofstra University',
    logo: hofstra,
    degree: 'Computer Engineering coursework, transferred to Cornell',
    dates: '2022 — 2023',
  },
];

export const honors = [
  {
    date: '2025',
    text: (
      <>
        Featured on Hackaday:{' '}
        <a href="https://hackaday.com/2025/06/27/audio-localization-gear-built-on-the-cheap/">
          “Audio Localization Gear Built on the Cheap”
        </a>
      </>
    ),
  },
  {
    date: '2019 — 2022',
    text: 'Innovation in Control Award, FIRST Robotics — four-time recipient',
  },
];
