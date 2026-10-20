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
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
