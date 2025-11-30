import React from 'react';
import { personalInfo, researchProjects, engineeringProjects, teachingExperience, industryExperience } from './data';
import Header from './components/Header';
import Research from './components/Research';
import Engineering from './components/Engineering';
import Experience from './components/Experience';
import Footer from './components/Footer';

function App() {
  return (
    <div className="app-container">
      <Header personalInfo={personalInfo} />
      <main>
        <Research projects={researchProjects} />
        <Engineering projects={engineeringProjects} />
        <Experience teaching={teachingExperience} industry={industryExperience} />
      </main>
      <Footer />
    </div>
  );
}

export default App;
