# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
I would include Owner, pet, and. scheduler class. In owner I would include name, and availability. For pet I would include name, age, gender, species  requirements and priority. Lastly for scheduler I would include done or not andcreate a daily plan. 
- What classes did you include, and what responsibilities did you assign to each?
I included 4 classes, owner, pet, task and scheduler. The owner class will show their availability with their list of pets. They have the availibility to add or remove tasks, and check whether it is done. The pet class include the general information (name, age, breed), then each pet would have an individual list of tasks that they need to have done and by what time, while including the priority of the task. After the task  class just explains the attributes of the class and whether it was complete. Lastly we have the scheduler which will create a daily plan for the owners including a checklist. 


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
I did make a lot of changes during implementation. One in particular is changing the way I implemented multiple people owning the same animals. Scheduler will now has household which is a class with multiple people who can complete the task.  
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
Constraints my scheduler considers is timing and priority, as it follows somewhat of a first come first serve basis. First it considers priority then time, and if they both are the same then it will decide based on which entered the systm first.
- How did you decide which constraints mattered most?
I decided to go with priority especially with pets who requires priority whether if its due to its breed or personality. 
**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
A tradeoff my scheduler makes is greedness, it can only manage one task at a time. 
- Why is that tradeoff reasonable for this scenario?
This tradeoff was reasonable on this scenerio because it allows the application to run/think quick. It provides a clear plan for the user, similiarily to a notepad if someone organized your tasks without knowing you at all. 

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
I used AI to understand the questions being asked, then once I fully understand the prompt I started designing. After designing I asked AI how I can improve the overall designs and what important factors I am missing. 
- What kinds of prompts or questions were most helpful?
Questions that were helpful were the ones that included explainations on why AI choose to to go with one decision versus the other. Reading through the code and questioning the decisions of AI helped fix minor logical mistakes within the first wave of changes. 

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
I decided not to do an AI suggestion was at the time availability attribute. In one of the tests it stated that "Jo" waw available from 7-9 am but the available_minutes was 60 minutes. I decided against this and have it reflect the same amount of time because it logically did not make sense. 
- How did you evaluate or verify what the AI suggested? I would evaluate the AI suggestions by looking on the local site to see if the changes were properly implemented. In cases where the UI is not implemented, I would ask AI to create test cases to determine if the code is producing correct results. 



## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
I tested the behaviors of adding a task, if warning signals will occur or not, generate a schedule based off priority/time. 
- Why were these tests important?
I believe that these tests are important to determine if the main components of the application is working. It tests scenerios like cases where multiple tasks occur at once, or when multiple people in the household complete a task.


**b. Confidence**

- How confident are you that your scheduler works correctly?
I would say that I was somewhat confident that my scheduler work, I definetly took time to make sure AI was changing the code
to my preferences while being logically correct. 
- What edge cases would you test next if you had more time?
Edge cases I would want to test is if there are multiple tasks at the same time and priority and to find methods to fix it. Another edge case I would test is letting others in the household (multiple owners) add or complete tasks. 

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
I am most satisfied with the warnings of the overlapping tasks. 

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
I would improve the household implementation, I felt that the logic made sense but I wasn't sure how it would be visually represented. 

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
One important thing I learned about designing systems is the different levels of relationships the classes may have with each other and how it is important to specify what access each class has. For example in the orginal diagram there was a case where pets were able to make tasks which logically did not make sense.
