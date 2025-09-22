// '새 문제 추가' 페이지의 모든 로직을 이 함수 안에 넣습니다.
function initializeAddQuestionPage() {
    // Select2 초기화
    $(document).ready(function() {
        $('#id_tags').select2({
            placeholder: "태그를 선택하거나 검색하세요",
            allowClear: true
        });
    });

    // 동적 카테고리 로직
    const examSelect = document.getElementById('id_exam');
    const categorySelect = document.getElementById('id_category');
    if (examSelect && categorySelect) {
        function fetchCategories() {
            const examId = examSelect.value;
            if (!examId) {
                categorySelect.innerHTML = '<option value="">---------</option>';
                return;
            }
            fetch(`/api/categories/${examId}/`)
                .then(response => response.json())
                .then(data => {
                    categorySelect.innerHTML = '<option value="">---------</option>';
                    data.forEach(category => {
                        const option = new Option(category.name, category.id);
                        categorySelect.add(option);
                    });
                });
        }
        examSelect.addEventListener('change', fetchCategories);
        if (examSelect.value) fetchCategories();
    }

    // 선택지 추가/제거 로직
    const optionsContainer = document.getElementById('options-container');
    const typeSelect = document.getElementById('id_type');
    if (optionsContainer && typeSelect) {
        function updateOptionsVisibility() {
            const selectedType = typeSelect.value;
            optionsContainer.style.display = (selectedType === 'MCQ' || selectedType === 'MA') ? 'block' : 'none';
        }
        updateOptionsVisibility();
        typeSelect.addEventListener('change', updateOptionsVisibility);

        const addOptionBtn = document.getElementById('add-option');
        const optionsFields = document.getElementById('options-fields');
        let optionCounter = optionsFields ? optionsFields.children.length : 0;

        if (addOptionBtn) {
            addOptionBtn.addEventListener('click', function () {
                optionCounter++;
                const newOptionDiv = document.createElement('div');
                newOptionDiv.className = 'input-group mb-3';
                newOptionDiv.innerHTML = `
                    <input type="text" name="option_${optionCounter}" class="form-control" placeholder="선택지 ${optionCounter}">
                    <button class="btn btn-outline-secondary remove-option" type="button">제거</button>
                `;
                optionsFields.appendChild(newOptionDiv);
            });
        }
        if (optionsFields) {
            optionsFields.addEventListener('click', function (event) {
                if (event.target.classList.contains('remove-option')) {
                    event.target.closest('.input-group').remove();
                }
            });
        }
    }

    // AI 검증 버튼 로직
    const aiValidateBtn = document.getElementById('ai-validate-btn');
    const addQuestionForm = document.getElementById('add-question-form');

    if (aiValidateBtn && addQuestionForm) {
        const aiFeedbackBox = document.getElementById('ai-feedback-box');
        const aiFeedbackContent = document.getElementById('ai-feedback-content');
        const csrfToken = addQuestionForm.querySelector('[name=csrfmiddlewaretoken]').value;
        const validateUrl = addQuestionForm.dataset.validateUrl;

        aiValidateBtn.addEventListener('click', function() {
            // Summernote 에디터에서 내용 가져오기
            const content = $('#id_content').summernote('code');
            const passage = $('#id_passage').summernote('code');
            const explanation = $('#id_explanation').summernote('code');

            // 다른 필드에서 값 가져오기
            const options = Array.from(document.querySelectorAll('[name^="option_"]')).map(input => input.value).join(', ');
            const answer = document.getElementById('id_correct_answer').value;

            // 로딩 상태 표시
            aiFeedbackContent.innerHTML = 'AI가 문제를 검증하고 있습니다... 잠시만 기다려주세요.';
            aiFeedbackBox.style.display = 'block';

            fetch(validateUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    'content': content,
                    'passage': passage,
                    'options': options,
                    'answer': answer,
                    'explanation': explanation
                })
            })
            .then(response => response.json())
            .then(data => {
                aiFeedbackContent.innerText = (data.status === 'success') ? data.feedback : '오류: ' + data.message;
            })
            .catch(error => {
                aiFeedbackContent.innerText = 'API를 호출하는 중 오류가 발생했습니다.';
                console.error('AI Validate Fetch Error:', error);
            });
        });
    }
}

function initializeQuizPage() {
    // 퀴즈/상세보기 페이지를 식별하는 컨테이너
    const pageContainer = document.getElementById('quiz-page-container');
    if (!pageContainer) return;

    // 필요한 모든 요소를 이 컨테이너 안에서 찾습니다.
    const questionId = pageContainer.dataset.questionId;
    const questionType = pageContainer.dataset.questionType;
    const isLastQuestion = pageContainer.dataset.isLastQuestion === 'true';
    const recordUrl = pageContainer.dataset.recordUrl;
    const summaryUrl = pageContainer.dataset.summaryUrl;

    const submitBtn = pageContainer.querySelector('#submit-btn');
    const nextBtn = pageContainer.querySelector('#next-btn');
    const explanationBox = pageContainer.querySelector('#explanation-box');
    const optionsContainer = pageContainer.querySelector('#options-container');
    const saAnswerInput = pageContainer.querySelector('#sa-answer-input');
    const correctAnswerEl = pageContainer.querySelector('#correct-answer');
    const csrfTokenEl = pageContainer.querySelector('form [name=csrfmiddlewaretoken]');

    if (!submitBtn || !nextBtn || !explanationBox || !correctAnswerEl || !csrfTokenEl) return;

    const correctAnswer = correctAnswerEl.dataset.answer;
    const csrfToken = csrfTokenEl.value;
    let selectedAnswer = null;

    if (optionsContainer) {
        optionsContainer.addEventListener('click', function (event) {
            const clickedOption = event.target.closest('.option');
            if (!clickedOption || submitBtn.style.display === 'none') return;

            if (questionType === 'MA') { // 복수정답
                clickedOption.classList.toggle('selected');
            } else { // 객관식
                optionsContainer.querySelectorAll('.option').forEach(opt => opt.classList.remove('selected'));
                clickedOption.classList.add('selected');
            }
            selectedAnswer = Array.from(optionsContainer.querySelectorAll('.option.selected'))
                                .map(opt => opt.dataset.value).sort().join(',');
        });
    }

    // 👇 '제출하기' 버튼 클릭 이벤트 (showResult 함수 포함)
    submitBtn.addEventListener('click', function () {
        if (questionType === 'SA') {
            selectedAnswer = saAnswerInput.value;
        }
        if (selectedAnswer === null || selectedAnswer.trim() === '') {
            alert('답안을 선택하거나 입력해주세요.');
            return;
        }

        const isQuizMode = pageContainer.dataset.quizMode === 'true';
        const finalRecordUrl = isQuizMode ? recordUrl : `/question/${questionId}/`;

        fetch(finalRecordUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ 'question_id': questionId, 'user_answer': selectedAnswer })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showResult(data.is_correct); // 결과 표시 함수 호출
            }
        });
    });

    // 👇 결과를 화면에 표시하는 함수
  function showResult(isCorrect) {
        if (optionsContainer) {
            const correctAnswers = correctAnswer.split(',').map(s => s.trim());
            optionsContainer.querySelectorAll('.option').forEach(opt => {
                if (correctAnswers.includes(opt.dataset.value)) {
                    opt.classList.add('correct');
                } else if (opt.classList.contains('selected')) {
                    opt.classList.add('incorrect');
                }
                opt.style.pointerEvents = 'none';
            });
        }
        if (saAnswerInput) {
            saAnswerInput.disabled = true;
            saAnswerInput.classList.add(isCorrect ? 'is-valid' : 'is-invalid');
        }

        // 정답/오답 메시지 생성 및 표시
        const resultMessage = document.createElement('div');
        resultMessage.className = `alert mt-4 ${isCorrect ? 'alert-success' : 'alert-danger'}`;

        let messageText = isCorrect ? '정답입니다! 🎉' : '틀렸습니다. 😭';

        // 👇 이 부분을 수정하여 객관식/주관식 정답을 모두 처리합니다.
        let answerHtml = '<strong>정답:</strong><br>';
        const correctAnswers = correctAnswer.split(',').map(s => s.trim());

        if (questionType === 'SA') {
            answerHtml += correctAnswers.join('<br>');
        } else { // MCQ, MA
            optionsContainer.querySelectorAll('.option').forEach(opt => {
                if (correctAnswers.includes(opt.dataset.value)) {
                    const optionLabel = opt.querySelector('b').innerText;
                    const optionText = opt.dataset.value;
                    answerHtml += `${optionLabel} ${optionText}<br>`;
                }
            });
        }

        messageText += `<br>${answerHtml}`;
        resultMessage.innerHTML = messageText;
        explanationBox.before(resultMessage);

        // UI 상태 변경
        explanationBox.style.display = 'block';
        submitBtn.style.display = 'none';

        const isQuizMode = pageContainer.dataset.quizMode === 'true';
        if (isQuizMode) {
            if (isLastQuestion) {
                nextBtn.innerText = '결과 보기';
                nextBtn.href = summaryUrl;
            }
        }
        nextBtn.style.display = 'inline-block';
    }
}



// 퀴즈 선택 페이지의 동적 문제 개수 표시 로직
function initializeQuizSelectPage() {
    const examSelect = document.getElementById('id_exam');
    const modeSelect = document.getElementById('id_mode');
    const availableCountSpan = document.getElementById('available-count');

    function updateAvailableCount() {
        const examId = examSelect.value;
        const mode = modeSelect.value;

        fetch(`/api/quiz/count/?exam=${examId}&mode=${mode}`)
            .then(response => response.json())
            .then(data => {
                const count = data.count;
                availableCountSpan.innerText = `(${count}개)`;
            })
            .catch(error => {
                console.error('문제 개수를 가져오는 중 오류 발생:', error);
                availableCountSpan.innerText = '(오류)';
            });
    }

    // 페이지 로드 시, 그리고 선택 값이 변경될 때마다 함수 실행
    if (examSelect && modeSelect && availableCountSpan) {
        examSelect.addEventListener('change', updateAvailableCount);
        modeSelect.addEventListener('change', updateAvailableCount);
        updateAvailableCount();
    }
}


// --- 페이지 로드 시 실행 ---
document.addEventListener('DOMContentLoaded', function () {
    // '새 문제 추가' 페이지의 경우, 모든 리소스(Summernote)가 로드된 후 실행
    if (document.getElementById('add-question-form')) {
            initializeAddQuestionPage();
    }
    // 그 외 페이지들은 DOM만 준비되면 바로 실행
    else {
        initializeQuizPage();
        initializeQuizSelectPage();
    }
});