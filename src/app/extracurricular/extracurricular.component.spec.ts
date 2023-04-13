import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ExtracurricularComponent } from './extracurricular.component';

describe('ExtracurricularComponent', () => {
  let component: ExtracurricularComponent;
  let fixture: ComponentFixture<ExtracurricularComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ExtracurricularComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ExtracurricularComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
