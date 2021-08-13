# Test files

Currently, there is a mix of tests using unittest and pytest.  Eventually they will all be migrated to use pytest.


## The directory `fixtures`
- The `test.nsx` file is a synology note station export file.  It has two notebooks, and some notes in the recycle bin and can be used for a basic end to end functional test.
  - Inside the `.nsx` export file a notebook called ```test``` has a note called 'test page'.  This page has an example of each feature available in Synology Note-Station notes.
  - The pdf file ```test page.pdf``` is what the test-page inside the nsx file looks like in Note-Station.


## The directory `test_chart_processing`
This contains 3 images that are regression tested for chart processing tests.


## The directory `fixtures`
Contains files used for unit test data input.

