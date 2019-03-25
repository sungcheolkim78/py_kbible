# py_kbible

python library to extract korean bible verse

한국어 성경 (개역개정판성경, 개역한글판성경, 등등) 을 Python에서 읽어 들여서 관련 정보를 처리할 수 있게 해주는 라이브러리

## Download source

저작권의 제약을 받지 않는 성경 버전을 찾기 위해 다음 사이트를 참조하였다. 특히나 한국어 성경은 `개역한글판성경`을 제외하고는 모두다 대한 성서공회에 저작권이 있다. `TODO` 대한 성서 공회에 문의를 하여서 문제가 있는지 확인하자. 영어 성경의 경우 `ASV (American Standard Version)`, `WEB (World English Bible)`등이 저작권의 문제가 없이 사용할 수 있다.

- [hackathon.bible](http://www.hackathon.bible/data.html)
- [bible4u.net](https://bible4u.net/en/download)

## Install

기본적으로 pandas를 이용해 Database를 관리하므로 설치되어 있지 않다면 pandas를 먼저 설치해 준다. 이 후에 github를 통해 설치할 수 있다. `TODO` pypi에 등록하여서 pip를 통해 설치할 수 있게 한다.

```
pip3 install pandas
pip3 install "https://github.com/sungcheolkim78/py_kbible.git"
```

올바르게 설치되었는지를 확인하기 위해서는 ipython이나 jupyter notebook에서 다음과 같이 실행해 본다.

```python
from py_kbible import kbible
b1 = kbible.KBible("개역개정판성경")
b1.add("WEB")
b1.extract_bystr("창1:1")
```

제대로 설치되었다면, 두가지 버전으로 pandas의 DataFrame으로 창세기 1장 1절이 출력될 것이다.

## Usage

우선 가장 중요한 것은 성경 text를 pandas의 DataFrame으로 저장하고 여기에 여러가지 search function을 적용해서 장, 절을 출력하게 하였다. 이 후에 이 데이터베이스를 기반으로 object class를 정의하고 각각의 함수를 호출하여 사용하게 하였다.

예를 들어 `개역한글판성경`, `JA1955` 버전의 성경을 연구하고 싶다면 다음과 같이 KBible object를 정의하고 관련 함수를 호출하면 된다.

```python
b = kbible.KBible("개역한글판성경")
b.add("JA1955")
print(b.search("다윗", form="md"))
```

마지막 줄에서 search method는 해당 단어를 성경에서 찾아주고 그 결과를 `md (markdown)`형식으로 출력해 준다.

