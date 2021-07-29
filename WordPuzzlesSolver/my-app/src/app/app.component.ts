import { Component, ElementRef } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ViewChild } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {

  @ViewChild('background', {static: false})
  backgroundVar: ElementRef;

  @ViewChild('grammar', {static: false})
  grammarVar: ElementRef;

  @ViewChild('question', {static: false})
  questionVar: ElementRef;

  title = 'app';

  buttonLabel: string[] = [];

  puzzleType: string = null;
  questionType: string = null;

  readonly ROOT_PATH = "http://127.0.0.1:5002/puzzle/";
  readonly QUESTION_PATH = "http://127.0.0.1:5002/question/";

  puzzleUrl: string;

  grammarFile: File = null;
  backgroundFile: File = null;
  questionFile: File = null;

  puzzlesFile: File = null;

  puzzles: string[] = [];
  questions: string[] = [];

  solution: string[] = [];
  showSolution: boolean[] = [];

  stringFromFile: string = "";
  puzzleFileName: string = "";
  questionFileName: string = "";

  puzzleFileUploaded: boolean = false;

  constructor(private httpClient: HttpClient) {
    
  }

  ngOnInit() {
  }

  solvePuzzle(i) {
    this.puzzleUrl = this.ROOT_PATH + this.puzzleType + (i + 1);

    if (this.backgroundFile == null || this.grammarFile == null) {
      alert("Please load background and grammar files");
    }

    this.httpClient.post<string>(this.puzzleUrl, {"puzzle": this.puzzles[i], "filepath": this.grammarFile.name, "background": this.backgroundFile.name}).subscribe(
      (val) => {
          console.log("POST call successful value returned in body", val);
          if (this.showSolution[i] == false) {
            this.solution[i] = ""
            this.showSolution[i] = true;
            this.buttonLabel[i] = "Solve puzzle";
          }
  
          else {
            this.solution[i] = "Solution: " + val;
            this.showSolution[i] = false;
            this.buttonLabel[i] = "Hide solving";
          }
            
        },
        response => {
            console.log("POST call in error", response);
            alert("Error! The puzzle could not be solved!");
        },
        () => {
            console.log("The POST observable is now completed.");
        });
    
  }

  backgroundUpload(files: FileList) {
    this.backgroundFile = null;
    this.backgroundFile = files.item(0);

    return this.backgroundFile;
  }

 
  grammarUpload(files: FileList) {
    this.grammarFile = null;
    this.grammarFile = files.item(0);

    return this.grammarFile;
  }

  
  questionUpload(files: FileList) {
    this.questions = [];
    this.questionFile = null;
    this.questionFile = files.item(0);

    this.questionFileName = this.questionFile.name;
    this.questionType = this.questionFileName.substr(0, this.questionFileName.lastIndexOf('.'));

    var reader = new FileReader();
    reader.onload = () => {
        this.stringFromFile = reader.result.toString();
        this.questions = this.stringFromFile.split("\r\n\r\n")

        for (let i = 0; i < this.questions.length; i++) {
          this.questions[i] = this.questions[i].replace("\r\n", "");
        }
        
    };

    reader.readAsText(this.questionFile);
  
  }
  
  loadPuzzles(files: FileList) {
    this.solution = [];
    this.showSolution = [];
    this.questions = [];

    if(this.backgroundVar) {
      this.backgroundVar.nativeElement.value = "";
    }

    if(this.grammarVar) {
      this.grammarVar.nativeElement.value = "";
    }

    if(this.questionVar) {
      this.questionVar.nativeElement.value = "";
    }

    this.grammarFile = null;
    this.backgroundFile = null;
    this.questionFile = null;
    this.puzzlesFile = null;
    this.puzzlesFile = files.item(0);

    this.puzzleFileName = this.puzzlesFile.name;
    this.puzzleType = this.puzzleFileName.substr(0, this.puzzleFileName.lastIndexOf('.'));
    this.puzzleFileUploaded = true;

    var reader = new FileReader();
    reader.onload = () => {
        this.stringFromFile = reader.result.toString();
        this.puzzles = this.stringFromFile.split("\r\n\r\n")

        for (let i = 0; i < this.puzzles.length; i++) {
          this.buttonLabel[i] = "Solve puzzle";
          this.puzzles[i] = this.puzzles[i].replace("\r\n", "");
        }
        
    };

    reader.readAsText(this.puzzlesFile);
  }


  proofStatement(i) {
    this.puzzleUrl = this.QUESTION_PATH + this.puzzleType + (i + 1);

    if (this.backgroundFile == null || this.grammarFile == null || this.questionFile == null) {
      alert("Please load background, grammar and question files");
    }

    this.httpClient.post<string>(this.puzzleUrl, {"puzzle": this.puzzles[i], "filepath": this.grammarFile.name, "background": this.backgroundFile.name, "question": this.questions[i]}).subscribe(
      (val) => {
        console.log("POST call successful value returned in body", val);

        alert("The proofs for your questions are in file " + val)
      },
      
      response => {
        console.log("POST call in error", response);
        alert("Error! The puzzle could not be solved!");
      },
      () => {
        console.log("The POST observable is now completed.");
      });
    
  }

}
