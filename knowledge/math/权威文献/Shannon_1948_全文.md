# A Mathematical Theory of Communication
**Author:** C. E. Shannon  
**Published:** Bell System Technical Journal, Vol. 27, pp. 379–423, 623–656, July/October 1948  
**Status:** 信息论奠基之作，10 万+引用

---

## Part I — Introduction


## Part I — Introduction

Reprinted with corrections from The Bell System Technical Journal,
V ol. 27, pp. 379--423, 623--656, July, October, 1948.
A Mathematical Theory of Communication
By C. E. SHANNON
INTRODUCTION
T
HE recent development of various methods of modulation such as PCM and PPM which exchange
bandwidth for signal-to-noise ratio has intensified the interest in a general theory of communication. A
basis for such a theory is contained in the important papers of Nyquist1 and Hartley2 on this subject. In the
present paper we will extend the theory to include a number of new factors, in particular the effect of noise
in the channel, and the savings possible due to the statistical structure of the original message and due to the
nature of the final destination of the information.
The fundamental problem of communication is that of reproducing at one point either exactly or ap-
proximately a message selected at another point. Frequently the messages have meaning; that is they refer
to or are correlated according to some system with certain physical or conceptual entities. These semantic
aspects of communication are irrelevant to the engineering problem. The significant aspect is that the actual
message is one selected from a set of possible messages. The system must be designed to operate for each
possible selection, not just the one which will actually be chosen since this is unknown at the time of design.
If the number of messages in the set is finite then this number or any monotonic function of this number
can be regarded as a measure of the information produced when one message is chosen from the set, all
choices being equally likely. As was pointed out by Hartley the most natural choice is the logarithmic
function. Although this definition must be generalized considerably when we consider the influence of the
statistics of the message and when we have a continuous range of messages, we will in all cases use an
essentially logarithmic measure.
The logarithmic measure is more convenient for various reasons:
1. It is practically more useful. Parameters of engineering importance such as time, bandwidth, number
of relays, etc., tend to vary linearly with the logarithm of the number of possibilities. For example,
adding one relay to a group doubles the number of possible states of the relays. It adds 1 to the base 2
logarithm of this number. Doubling the time roughly squares the number of possible messages, or
doubles the logarithm, etc.
2. It is nearer to our intuitive feeling as to the proper measure. This is closely related to (1) since we in-
tuitively measures entities by linear comparison with common standards. One feels, for example, that
two punched cards should have twice the capacity of one for information storage, and two identical
channels twice the capacity of one for transmitting information.
3. It is mathematically more suitable. Many of the limiting operations are simple in terms of the loga-
rithm but would require clumsy restatement in terms of the number of possibilities.
The choice of a logarithmic base corresponds to the choice of a unit for measuring information. If the
base 2 is used the resulting units may be called binary digits, or more briefly bits, a word suggested by
J. W. Tukey. A device with two stable positions, such as a relay or a flip-flop circuit, can store one bit of
information. N such devices can storeN bits, since the total number of possible states is 2
N and log2 2N
/= N.
If the base 10 is used the units may be called decimal digits. Since
log2 M /= log10 M/= log10 2
/= 3/: 32log10 M/;
1Nyquist, H., "Certain Factors Affecting Telegraph Speed,"Bell System Technical Journal, April 1924, p. 324; "Certain Topics in
Telegraph Transmission Theory,"A.I.E.E. Trans., v. 47, April 1928, p. 617.
2Hartley, R. V . L., "Transmission of Information,"Bell System Technical Journal,July 1928, p. 535.

INFORMATION
SOURCE
MESSAGE
TRANSMI TTER
SIGNAL RECEIVED
SIGNAL
RECEIVER
MESSAGE
DESTINATION
NOISE
SOURCE
Fig. 1---Schematic diagram of a general communication system.
a decimal digit is about 3 1
3 bits. A digit wheel on a desk computing machine has ten stable positions and
therefore has a storage capacity of one decimal digit. In analytical work where integration and differentiation
are involved the base e is sometimes useful. The resulting units of information will be called natural units.
Change from the base a to base b merely requires multiplication by logb a.
By a communication system we will mean a system of the type indicated schematically in Fig. 1. It
consists of essentially five parts:
1. An information sourcewhich produces a message or sequence of messages to be communicated to the
receiving terminal. The message may be of various types: (a) A sequence of letters as in a telegraph
of teletype system; (b) A single function of time f
/#28 t/#29 as in radio or telephony; (c) A function of
time and other variables as in black and white television --- here the message may be thought of as a
function f /#28 x/; y/; t/#29 of two space coordinates and time, the light intensity at point /#28 x/; y/#29 and time t on a
pickup tube plate; (d) Two or more functions of time, say f /#28 t/#29 , g/#28 t/#29 , h/#28 t/#29 --- this is the case in "three-
dimensional" sound transmission or if the system is intended to service several individual channels in
multiplex; (e) Several functions of several variables --- in color television the message consists of three
functions f
/#28 x/; y/; t/#29 , g/#28 x/; y/; t/#29 , h/#28 x/; y/; t/#29 defined in a three-dimensional continuum --- we may also think
of these three functions as components of a vector field defined in the region --- similarly, several
black and white television sources would produce "messages" consisting of a number of functions
of three variables; (f) Various combinations also occur, for example in television with an associated
audio channel.
2. A transmitter which operates on the message in some way to produce a signal suitable for trans-
mission over the channel. In telephony this operation consists merely of changing sound pressure
into a proportional electrical current. In telegraphy we have an encoding operation which produces
a sequence of dots, dashes and spaces on the channel corresponding to the message. In a multiplex
PCM system the different speech functions must be sampled, compressed, quantized and encoded,
and finally interleaved properly to construct the signal. V ocoder systems, television and frequency
modulation are other examples of complex operations applied to the message to obtain the signal.
3. The channel is merely the medium used to transmit the signal from transmitter to receiver. It may be
a pair of wires, a coaxial cable, a band of radio frequencies, a beam of light, etc.
4. The receiver ordinarily performs the inverse operation of that done by the transmitter, reconstructing
the message from the signal.
5. The destination is the person (or thing) for whom the message is intended.
We wish to consider certain general problems involving communication systems. To do this it is first
necessary to represent the various elements involved as mathematical entities, suitably idealized from their


## Part I — Discrete Noiseless Systems

physical counterparts. We may roughly classify communication systems into three main categories: discrete,
continuous and mixed. By a discrete system we will mean one in which both the message and the signal
are a sequence of discrete symbols. A typical case is telegraphy where the message is a sequence of letters
and the signal a sequence of dots, dashes and spaces. A continuous system is one in which the message and
signal are both treated as continuous functions, e.g., radio or television. A mixed system is one in which
both discrete and continuous variables appear, e.g., PCM transmission of speech.
We first consider the discrete case. This case has applications not only in communication theory, but
also in the theory of computing machines, the design of telephone exchanges and other fields. In addition
the discrete case forms a foundation for the continuous and mixed cases which will be treated in the second
half of the paper.
PART I: DISCRETE NOISELESS SYSTEMS
1. T HE DISCRETE NOISELESS CHANNEL
Teletype and telegraphy are two simple examples of a discrete channel for transmitting information. Gen-
erally, a discrete channel will mean a system whereby a sequence of choices from a finite set of elementary
symbols S
/;/:/:/: /; Sn can be transmitted from one point to another. Each of the symbols Si is assumed to have
a certain duration in time ti seconds (not necessarily the same for different Si, for example the dots and
dashes in telegraphy). It is not required that all possible sequences of the Si be capable of transmission on
the system; certain sequences only may be allowed. These will be possible signals for the channel. Thus
in telegraphy suppose the symbols are: (1) A dot, consisting of line closure for a unit of time and then line
open for a unit of time; (2) A dash, consisting of three time units of closure and one unit open; (3) A letter
space consisting of, say, three units of line open; (4) A word space of six units of line open. We might place
the restriction on allowable sequences that no spaces follow each other (for if two letter spaces are adjacent,
it is identical with a word space). The question we now consider is how one can measure the capacity of
such a channel to transmit information.
In the teletype case where all symbols are of the same duration, and any sequence of the 32 symbols
is allowed the answer is easy. Each symbol represents five bits of information. If the system transmits n
symbols per second it is natural to say that the channel has a capacity of 5 n bits per second. This does not
mean that the teletype channel will always be transmitting information at this rate --- this is the maximum
possible rate and whether or not the actual rate reaches this maximum depends on the source of information
which feeds the channel, as will appear later.
In the more general case with different lengths of symbols and constraints on the allowed sequences, we
make the following definition:
Definition: The capacity C of a discrete channel is given by
C
/= Lim
T /! ∞
logN/#28 T /#29
T
where N/#28 T /#29 is the number of allowed signals of duration T.
It is easily seen that in the teletype case this reduces to the previous result. It can be shown that the limit
in question will exist as a finite number in most cases of interest. Suppose all sequences of the symbols
S
/;/:/:/: /; Sn are allowed and these symbols have durations t1
/;/:/:/: /; tn. What is the channel capacity? If N/#28 t/#29
represents the number of sequences of duration t we have
N/#28 t/#29/= N/#28 t /, t1
/#29/+ N/#28 t /, t2
/#29/+ /#01/#01/#01 /+ N/#28 t /, tn
/#29 /:
The total number is equal to the sum of the numbers of sequences ending in S1
/; S2
/;/:/:/: /; Sn and these are
N/#28 t /, t1
/#29 /; N/#28 t /, t2
/#29 /;/:/:/: /; N/#28 t /, tn
/#29 , respectively. According to a well-known result in finite differences, N/#28 t/#29
is then asymptotic for large t to Xt
0 where X0 is the largest real solution of the characteristic equation:
X
/, t1
/+ X
/, t2
/+ /#01/#01/#01 /+ X
/, tn
/= 1

and therefore
C /= logX0
/:
In case there are restrictions on allowed sequences we may still often obtain a difference equation of this
type and find C from the characteristic equation. In the telegraphy case mentioned above
N/#28 t/#29/= N/#28 t /, 2/#29/+ N/#28 t /, 4/#29/+ N/#28 t /, 5/#29/+ N/#28 t /, 7/#29/+ N/#28 t /, 8/#29/+ N/#28 t /, 10/#29
as we see by counting sequences of symbols according to the last or next to the last symbol occurring.
Hence C is /, log /#16
0 where /#16
0 is the positive root of 1 /= /#16
/+ /#16
/+ /#16
/+ /#16
/+ /#16
/+ /#16
10. Solving this we find
C /= 0/: 539.
A very general type of restriction which may be placed on allowed sequences is the following: We
imagine a number of possible statesa1
/; a2
/;/:/:/: /; am. For each state only certain symbols from the setS1
/;/:/:/: /; Sn
can be transmitted (different subsets for the different states). When one of these has been transmitted the
state changes to a new state depending both on the old state and the particular symbol transmitted. The
telegraph case is a simple example of this. There are two states depending on whether or not a space was
the last symbol transmitted. If so, then only a dot or a dash can be sent next and the state always changes.
If not, any symbol can be transmitted and the state changes if a space is sent, otherwise it remains the same.
The conditions can be indicated in a linear graph as shown in Fig. 2. The junction points correspond to the
DASH
DOT
DASH
DOT
LETTER SPACE
WORD SPACE
Fig. 2---Graphical representation of the constraints on telegraph symbols.
states and the lines indicate the symbols possible in a state and the resulting state. In Appendix 1 it is shown
that if the conditions on allowed sequences can be described in this form C will exist and can be calculated
in accordance with the following result:
Theorem 1: Let b
/#28 s/#29
ij be the duration of the sth symbol which is allowable in state i and leads to state j.
Then the channel capacity C is equal to logW where W is the largest real root of the determinant equation:
/#0C
/#0C
/#0C
∑
s
W
/, b
/#28 s/#29
ij
/, /#0E
ij
/#0C
/#0C
/#0C
/= 0
where /#0E
ij
/= 1 if i /= j and is zero otherwise.
For example, in the telegraph case (Fig. 2) the determinant is:
/#0C
/#0C
/#0C
/#0C
/,
1 /#28 W
/, 2
/+ W
/, 4
/#29
/#28 W
/, 3
/+ W
/, 6
/#29 /#28 W
/, 2
/+ W
/, 4
/, 1/#29
/#0C
/#0C
/#0C
/#0C
/=
0/:
On expansion this leads to the equation given above for this case.
2. T HE DISCRETE SOURCE OF INFORMATION
We have seen that under very general conditions the logarithm of the number of possible signals in a discrete
channel increases linearly with time. The capacity to transmit information can be specified by giving this
rate of increase, the number of bits per second required to specify the particular signal used.
We now consider the information source. How is an information source to be described mathematically,
and how much information in bits per second is produced in a given source? The main point at issue is the
effect of statistical knowledge about the source in reducing the required capacity of the channel, by the use

of proper encoding of the information. In telegraphy, for example, the messages to be transmitted consist of
sequences of letters. These sequences, however, are not completely random. In general, they form sentences
and have the statistical structure of, say, English. The letter E occurs more frequently than Q, the sequence
TH more frequently than XP, etc. The existence of this structure allows one to make a saving in time (or
channel capacity) by properly encoding the message sequences into signal sequences. This is already done
to a limited extent in telegraphy by using the shortest channel symbol, a dot, for the most common English
letter E; while the infrequent letters, Q, X, Z are represented by longer sequences of dots and dashes. This
idea is carried still further in certain commercial codes where common words and phrases are represented
by four- or five-letter code groups with a considerable saving in average time. The standardized greeting
and anniversary telegrams now in use extend this to the point of encoding a sentence or two into a relatively
short sequence of numbers.
We can think of a discrete source as generating the message, symbol by symbol. It will choose succes-
sive symbols according to certain probabilities depending, in general, on preceding choices as well as the
particular symbols in question. A physical system, or a mathematical model of a system which produces
such a sequence of symbols governed by a set of probabilities, is known as a stochastic process.
3 We may
consider a discrete source, therefore, to be represented by a stochastic process. Conversely, any stochastic
process which produces a discrete sequence of symbols chosen from a finite set may be considered a discrete
source. This will include such cases as:
1. Natural written languages such as English, German, Chinese.
2. Continuous information sources that have been rendered discrete by some quantizing process. For
example, the quantized speech from a PCM transmitter, or a quantized television signal.
3. Mathematical cases where we merely define abstractly a stochastic process which generates a se-
quence of symbols. The following are examples of this last type of source.
(A) Suppose we have five letters A, B, C, D, E which are chosen each with probability .2, successive
choices being independent. This would lead to a sequence of which the following is a typical
example.
BDCBCECCCADCBDDAAECEEA
ABBDAEECACEEBAEECBCEAD .
This was constructed with the use of a table of random numbers.
(B) Using the same five letters let the probabilities be .4, .1, .2, .2, .1, respectively, with successive
choices independent. A typical message from this source is then:
AAACDCBDCEAADADACEDA
EADCABEDADDCECAAAAAD .
(C) A more complicated structure is obtained if successive symbols are not chosen independently
but their probabilities depend on preceding letters. In the simplest case of this type a choice
depends only on the preceding letter and not on ones before that. The statistical structure can
then be described by a set of transition probabilitiespi
/#28 j/#29 , the probability that letteri is followed
by letter j. The indices i and j range over all the possible symbols. A second equivalent way of
specifying the structure is to give the "digram" probabilitiesp/#28 i/; j/#29 , i.e., the relative frequency of
the digram ij . The letter frequencies p/#28 i/#29 , (the probability of letteri), the transition probabilities
3See, for example, S. Chandrasekhar, "Stochastic Problems in Physics and Astronomy,"Reviews of Modern Physics, v. 15, No. 1,
January 1943, p. 1.
4Kendall and Smith, Tables of Random Sampling Numbers,Cambridge, 1939.

pi
/#28 j/#29 and the digram probabilities p/#28 i/; j/#29 are related by the following formulas:
p/#28 i/#29/=
∑
j
p/#28 i/; j/#29/=
∑
j
p/#28 j/; i/#29/=
∑
j
p/#28 j/#29 pj
/#28 i/#29
p/#28 i/; j/#29/= p/#28 i/#29 pi
/#28 j/#29
∑
j
pi
/#28 j/#29/=
∑
i
p/#28 i/#29/=
∑
i/; j
p/#28 i/; j/#29/= 1/:
As a specific example suppose there are three letters A, B, C with the probability tables:
pi
/#28 j/#29 j
AB C
A 0 4
i B 1
2 0
C 1
i p/#28 i/#29
A 9
B 16
C 2
p/#28 i/; j/#29 j
AB C
A 0 4
i B 8
27 0
C 1
A typical message from this source is the following:
ABBABABABABABABBBABBBBBABABABABABBBACACAB
BABBBBABBABACBBBABA .
The next increase in complexity would involve trigram frequencies but no more. The choice of
a letter would depend on the preceding two letters but not on the message before that point. A
set of trigram frequencies p
/#28 i/; j/; k/#29 or equivalently a set of transition probabilities pij
/#28 k/#29 would
be required. Continuing in this way one obtains successively more complicated stochastic pro-
cesses. In the general n-gram case a set of n-gram probabilities p/#28 i1
/; i2
/;/:/:/: /; in
/#29 or of transition
probabilities pi1
/; i2
/;/:/:/:/; in/, 1
/#28 in
/#29 is required to specify the statistical structure.
(D) Stochastic processes can also be defined which produce a text consisting of a sequence of
"words." Suppose there are five letters A, B, C, D, E and 16 "words" in the language with
associated probabilities:
.10 A .16 BEBE .11 CABED .04 DEB
.04 ADEB .04 BED .05 CEED .15 DEED
.05 ADEE .02 BEED .08 DAB .01 EAB
.01 BADD .05 CA .04 DAD .05 EE
Suppose successive "words" are chosen independently and are separated by a space. A typical
message might be:
DAB EE A BEBE DEED DEB ADEE ADEE EE DEB BEBE BEBE BEBE ADEE BED DEED
DEED CEED ADEE A DEED DEED BEBE CABED BEBE BED DAB DEED ADEB.
If all the words are of finite length this process is equivalent to one of the preceding type, but
the description may be simpler in terms of the word structure and probabilities. We may also
generalize here and introduce transition probabilities between words, etc.
These artificial languages are useful in constructing simple problems and examples to illustrate vari-
ous possibilities. We can also approximate to a natural language by means of a series of simple artificial
languages. The zero-order approximation is obtained by choosing all letters with the same probability and
independently. The first-order approximation is obtained by choosing successive letters independently but
each letter having the same probability that it has in the natural language.
5 Thus, in the first-order ap-
proximation to English, E is chosen with probability .12 (its frequency in normal English) and W with
probability .02, but there is no influence between adjacent letters and no tendency to form the preferred
5Letter, digram and trigram frequencies are given inSecret and Urgentby Fletcher Pratt, Blue Ribbon Books, 1939. Word frequen-
cies are tabulated in Relative Frequency of English Speech Sounds,G. Dewey, Harvard University Press, 1923.

digrams such as TH, ED, etc. In the second-order approximation, digram structure is introduced. After a
letter is chosen, the next one is chosen in accordance with the frequencies with which the various letters
follow the first one. This requires a table of digram frequencies p
i
/#28 j/#29 . In the third-order approximation,
trigram structure is introduced. Each letter is chosen with probabilities which depend on the preceding two
letters.
3. T HE SERIES OF APPROXIMATIONS TO ENGLISH
To give a visual idea of how this series of processes approaches a language, typical sequences in the approx-
imations to English have been constructed and are given below. In all cases we have assumed a 27-symbol
"alphabet," the 26 letters and a space.
1. Zero-order approximation (symbols independent and equiprobable).
XFOML RXKHRJFFJUJ ZLPWCFWKCYJ FFJEYVKCQSGHYD QPAAMKBZAACIBZL-
HJQD.
2. First-order approximation (symbols independent but with frequencies of English text).
OCRO HLI RGWR NMIELWIS EU LL NBNESEBY A TH EEI ALHENHTTPA OOBTTV A
NAH BRL.
3. Second-order approximation (digram structure as in English).
ON IE ANTSOUTINYS ARE T INCTORE ST BE S DEAMY ACHIN D ILONASIVE TU-
COOWE AT TEASONARE FUSO TIZIN ANDY TOBE SEACE CTISBE.
4. Third-order approximation (trigram structure as in English).
IN NO IST LAT WHEY CRATICT FROURE BIRS GROCID PONDENOME OF DEMONS-
TURES OF THE REPTAGIN IS REGOACTIONA OF CRE.
5. First-order word approximation. Rather than continue with tetragram, /:/:/: , n-gram structure it is easier
and better to jump at this point to word units. Here words are chosen independently but with their
appropriate frequencies.
REPRESENTING AND SPEEDILY IS AN GOOD APT OR COME CAN DIFFERENT NAT-
URAL HERE HE THE A IN CAME THE TO OF TO EXPERT GRAY COME TO FURNISHES
THE LINE MESSAGE HAD BE THESE.
6. Second-order word approximation. The word transition probabilities are correct but no further struc-
ture is included.
THE HEAD AND IN FRONTAL ATTACK ON AN ENGLISH WRITER THAT THE CHAR-
ACTER OF THIS POINT IS THEREFORE ANOTHER METHOD FOR THE LETTERS THAT
THE TIME OF WHO EVER TOLD THE PROBLEM FOR AN UNEXPECTED.
The resemblance to ordinary English text increases quite noticeably at each of the above steps. Note that
these samples have reasonably good structure out to about twice the range that is taken into account in their
construction. Thus in (3) the statistical process insures reasonable text for two-letter sequences, but four-
letter sequences from the sample can usually be fitted into good sentences. In (6) sequences of four or more
words can easily be placed in sentences without unusual or strained constructions. The particular sequence
of ten words "attack on an English writer that the character of this" is not at all unreasonable. It appears then
that a sufficiently complex stochastic process will give a satisfactory representation of a discrete source.
The first two samples were constructed by the use of a book of random numbers in conjunction with
(for example 2) a table of letter frequencies. This method might have been continued for (3), (4) and (5),
since digram, trigram and word frequency tables are available, but a simpler equivalent method was used.

To construct (3) for example, one opens a book at random and selects a letter at random on the page. This
letter is recorded. The book is then opened to another page and one reads until this letter is encountered.
The succeeding letter is then recorded. Turning to another page this second letter is searched for and the
succeeding letter recorded, etc. A similar process was used for (4), (5) and (6). It would be interesting if
further approximations could be constructed, but the labor involved becomes enormous at the next stage.
4. G
RAPHICAL REPRESENTATION OF A MARKOFF PROCESS
Stochastic processes of the type described above are known mathematically as discrete Markoff processes
and have been extensively studied in the literature. 6 The general case can be described as follows: There
exist a finite number of possible "states" of a system; S1
/; S2
/;/:/:/: /; Sn. In addition there is a set of transition
probabilities; pi
/#28 j/#29 the probability that if the system is in state Si it will next go to state Sj. To make this
Markoff process into an information source we need only assume that a letter is produced for each transition
from one state to another. The states will correspond to the "residue of influence" from preceding letters.
The situation can be represented graphically as shown in Figs. 3, 4 and 5. The "states" are the junction
A
B
C
D
E
/./1
/./1
/./2
/./2
/./4
Fig. 3---A graph corresponding to the source in example B.
points in the graph and the probabilities and letters produced for a transition are given beside the correspond-
ing line. Figure 3 is for the example B in Section 2, while Fig. 4 corresponds to the example C. In Fig. 3
A
A
B
B
BC
C
/./1
/./5
/./5
/./5
/./2
/./8
/./4
Fig. 4---A graph corresponding to the source in example C.
there is only one state since successive letters are independent. In Fig. 4 there are as many states as letters.
If a trigram example were constructed there would be at most n2 states corresponding to the possible pairs
of letters preceding the one being chosen. Figure 5 is a graph for the case of word structure in example D.
Here S corresponds to the "space" symbol.
5. E
RGODIC AND MIXED SOURCES
As we have indicated above a discrete source for our purposes can be considered to be represented by a
Markoff process. Among the possible discrete Markoff processes there is a group with special properties
of significance in communication theory. This special class consists of the "ergodic" processes and we
shall call the corresponding sources ergodic sources. Although a rigorous definition of an ergodic process is
somewhat involved, the general idea is simple. In an ergodic process every sequence produced by the process
6For a detailed treatment see M. Fr´echet, M´ethode des fonctions arbitraires. Th´eorie des ´ev´enements en chaˆıne dans le cas d'un
nombre fini d'´etats possibles. Paris, Gauthier-Villars, 1938.

is the same in statistical properties. Thus the letter frequencies, digram frequencies, etc., obtained from
particular sequences, will, as the lengths of the sequences increase, approach definite limits independent
of the particular sequence. Actually this is not true of every sequence but the set for which it is false has
probability zero. Roughly the ergodic property means statistical homogeneity.
All the examples of artificial languages given above are ergodic. This property is related to the structure
of the corresponding graph. If the graph has the following two properties
7 the corresponding process will
be ergodic:
1. The graph does not consist of two isolated parts A and B such that it is impossible to go from junction
points in part A to junction points in part B along lines of the graph in the direction of arrows and also
impossible to go from junctions in part B to junctions in part A.
2. A closed series of lines in the graph with all arrows on the lines pointing in the same orientation will
be called a "circuit." The "length" of a circuit is the number of lines in it. Thus in Fig. 5 series BEBES
is a circuit of length 5. The second property required is that the greatest common divisor of the lengths
of all circuits in the graph be one.
S
S
S
A
A
A
A
A
B
B
B
B
B
BB
C
D
D
D
D
D
D
E
E
E
E
E
E
E
E
E
E
E
Fig. 5---A graph corresponding to the source in example D.
If the first condition is satisfied but the second one violated by having the greatest common divisor equal
to d /#3E 1, the sequences have a certain type of periodic structure. The various sequences fall into d different
classes which are statistically the same apart from a shift of the origin (i.e., which letter in the sequence is
called letter 1). By a shift of from 0 up to d /, 1 any sequence can be made statistically equivalent to any
other. A simple example with d /= 2 is the following: There are three possible letters a/; b/; c. Letter a is
followed with either b or c with probabilities 1
3 and 2
3 respectively. Either b or c is always followed by letter
a. Thus a typical sequence is
abacacacabacababacac /:
This type of situation is not of much importance for our work.
If the first condition is violated the graph may be separated into a set of subgraphs each of which satisfies
the first condition. We will assume that the second condition is also satisfied for each subgraph. We have in
this case what may be called a "mixed" source made up of a number of pure components. The components
correspond to the various subgraphs. If L1, L2, L3
/;/:/:/: are the component sources we may write
L /= p1L1
/+ p2L2
/+ p3L3
/+ /#01/#01/#01
7These are restatements in terms of the graph of conditions given in Fr´echet.

where pi is the probability of the component source Li.
Physically the situation represented is this: There are several different sources L1, L2, L3
/;/:/:/: which are
each of homogeneous statistical structure (i.e., they are ergodic). We do not know ap r i o r iwhich is to be
used, but once the sequence starts in a given pure component Li, it continues indefinitely according to the
statistical structure of that component.
As an example one may take two of the processes defined above and assume p1
/= /: 2a n d p2
/= /: 8. A
sequence from the mixed source
L /= /: 2L1
/+ /: 8L2
would be obtained by choosing first L1 or L2 with probabilities .2 and .8 and after this choice generating a
sequence from whichever was chosen.
Except when the contrary is stated we shall assume a source to be ergodic. This assumption enables one
to identify averages along a sequence with averages over the ensemble of possible sequences (the probability
of a discrepancy being zero). For example the relative frequency of the letter A in a particular infinite
sequence will be, with probability one, equal to its relative frequency in the ensemble of sequences.
If P
i is the probability of state i and pi
/#28 j/#29 the transition probability to state j, then for the process to be
stationary it is clear that the Pi must satisfy equilibrium conditions:
Pj
/=
∑
i
Pi pi
/#28 j/#29 /:
In the ergodic case it can be shown that with any starting conditions the probabilitiesPj
/#28 N/#29 of being in state
j after N symbols, approach the equilibrium values as N /! ∞ .
6. C HOICE ,U NCERTAINTY AND ENTROPY
We have represented a discrete information source as a Markoff process. Can we define a quantity which
will measure, in some sense, how much information is "produced" by such a process, or better, at what rate
information is produced?
Suppose we have a set of possible events whose probabilities of occurrence are p
/; p2
/;/:/:/: /; pn.T h e s e
probabilities are known but that is all we know concerning which event will occur. Can we find a measure
of how much "choice" is involved in the selection of the event or of how uncertain we are of the outcome?
If there is such a measure, sayH/#28 p1
/; p2
/;/:/:/:/; pn
/#29 , it is reasonable to require of it the following properties:
1. H should be continuous in the pi.
2. If all the pi are equal, pi
/=
n ,t h e nH should be a monotonic increasing function of n. With equally
likely events there is more choice, or uncertainty, when there are more possible events.
3. If a choice be broken down into two successive choices, the original H should be the weighted sum
of the individual values of H. The meaning of this is illustrated in Fig. 6. At the left we have three
/1/#2F/2
/1/#2F/3
/1/#2F/6
/1/#2F/2
/1/#2F/2
/2/#2F/3
/1/#2F/3
/1/#2F/2
/1/#2F/3
/1/#2F/6
Fig. 6---Decomposition of a choice from three possibilities.
possibilities p1
/=
2 , p2
/=
3 , p3
/=
6 . On the right we first choose between two possibilities each with
probability 1
2 , and if the second occurs make another choice with probabilities 2
3 , 1
3 . The final results
have the same probabilities as before. We require, in this special case, that
H/#28
/;
/;
/#29/= H/#28
/;
/#29/+
2 H/#28
/;
/#29 /:
The coefficient 1
2 is because this second choice only occurs half the time.

In Appendix 2, the following result is established:
Theorem 2: The only H satisfying the three above assumptions is of the form:
H /= /, K
n
∑
i/= 1
pi log pi
where K is a positive constant.
This theorem, and the assumptions required for its proof, are in no way necessary for the present theory.
It is given chiefly to lend a certain plausibility to some of our later definitions. The real justification of these
definitions, however, will reside in their implications.
Quantities of the formH /= /,
∑ pi log pi (the constant K merely amounts to a choice of a unit of measure)
play a central role in information theory as measures of information, choice and uncertainty. The form ofH
will be recognized as that of entropy as defined in certain formulations of statistical mechanics8 where pi is
the probability of a system being in cell i of its phase space. H is then, for example, the H in Boltzmann's
famous H theorem. We shall call H /= /,
∑ pi log pi the entropy of the set of probabilities p1
/;/:/:/: /; pn.I f x is a
chance variable we will write H/#28 x/#29 for its entropy; thus x is not an argument of a function but a label for a
number, to differentiate it from H/#28 y/#29 say, the entropy of the chance variabley.
The entropy in the case of two possibilities with probabilities p and q /= 1 /, p, namely
H /= /, /#28 plog p /+ qlogq/#29
is plotted in Fig. 7 as a function of p.
H
BITS
p
/0
/./1
/./2
/./3
/./4
/./5
/./6
/./7
/./8
/./9
/1/./0
/0 /./1 /./2 /./3 /./4 /./5 /./6 /./7 /./8 /./9 /1/./0
Fig. 7---Entropy in the case of two possibilities with probabilities p and /#28 1 /, p/#29 .
The quantity H has a number of interesting properties which further substantiate it as a reasonable
measure of choice or information.
1. H /= 0 if and only if all the pi but one are zero, this one having the value unity. Thus only when we
are certain of the outcome does H vanish. Otherwise H is positive.
2. For a given n, H is a maximum and equal to log n when all the pi are equal (i.e., 1
n ). This is also
intuitively the most uncertain situation.
8See, for example, R. C. Tolman,Principles of Statistical Mechanics, Oxford, Clarendon, 1938.

3. Suppose there are two events,x and y, in question withm possibilities for the first andn for the second.
Let p/#28 i/; j/#29 be the probability of the joint occurrence ofi for the first and j for the second. The entropy of the
joint event is
H/#28 x/; y/#29/= /,
∑
i/; j
p/#28 i/; j/#29 log p/#28 i/; j/#29
while
H/#28 x/#29/= /,
∑
i/; j
p/#28 i/; j/#29 log ∑
j
p/#28 i/; j/#29
H/#28 y/#29/= /,
∑
i/; j
p/#28 i/; j/#29 log ∑
i
p/#28 i/; j/#29 /:
It is easily shown that
H/#28 x/; y/#29 /#14 H/#28 x/#29/+ H/#28 y/#29
with equality only if the events are independent (i.e., p/#28 i/; j/#29/= p/#28 i/#29 p/#28 j/#29 ). The uncertainty of a joint event is
less than or equal to the sum of the individual uncertainties.
4. Any change toward equalization of the probabilities p1
/; p2
/;/:/:/: /; pn increases H. Thus if p1
/#3C p2 and
we increase p1, decreasing p2 an equal amount so that p1 and p2 are more nearly equal, then H increases.
More generally, if we perform any "averaging" operation on thepi of the form
p
/0
i
/=
∑
j
aij pj
where ∑ i aij
/=
∑ j aij
/= 1, and all aij
/#15 0, then H increases (except in the special case where this transfor-
mation amounts to no more than a permutation of the pj with H of course remaining the same).
5. Suppose there are two chance events x and y as in 3, not necessarily independent. For any particular
value i that x can assume there is a conditional probability pi
/#28 j/#29 that y has the value j. This is given by
pi
/#28 j/#29/=
p/#28 i/; j/#29
∑ j p/#28 i/; j/#29
/:
We define the conditional entropyof y, Hx
/#28 y/#29 as the average of the entropy ofy for each value ofx, weighted
according to the probability of getting that particular x.T h a ti s
Hx
/#28 y/#29/= /,
∑
i/; j
p/#28 i/; j/#29 log pi
/#28 j/#29 /:
This quantity measures how uncertain we are ofy on the average when we knowx. Substituting the value of
pi
/#28 j/#29 we obtain
Hx
/#28 y/#29/= /,
∑
i/; j
p/#28 i/; j/#29 log p/#28 i/; j/#29/+
∑
i/; j
p/#28 i/; j/#29 log∑
j
p/#28 i/; j/#29
/= H/#28 x/; y/#29 /, H/#28 x/#29
or
H/#28 x/; y/#29/= H/#28 x/#29/+ Hx
/#28 y/#29 /:
The uncertainty (or entropy) of the joint event x/; y is the uncertainty of x plus the uncertainty of y when x is
known.
6. From 3 and 5 we have
H/#28 x/#29/+ H/#28 y/#29 /#15 H/#28 x/; y/#29/= H/#28 x/#29/+ Hx
/#28 y/#29 /:
Hence
H/#28 y/#29 /#15 Hx
/#28 y/#29 /:
The uncertainty ofy is never increased by knowledge ofx. It will be decreased unlessx and y are independent
events, in which case it is not changed.

7. T HE ENTROPY OF AN INFORMATION SOURCE
Consider a discrete source of the finite state type considered above. For each possible state i there will be a
set of probabilities pi
/#28 j/#29 of producing the various possible symbols j. Thus there is an entropy Hi for each
state. The entropy of the source will be defined as the average of these Hi weighted in accordance with the
probability of occurrence of the states in question:
H /=
∑
i
PiHi
/= /,
∑
i/; j
Pi pi
/#28 j/#29 log pi
/#28 j/#29 /:
This is the entropy of the source per symbol of text. If the Markoff process is proceeding at a definite time
rate there is also an entropy per second
H
/0
/=
∑
i
fiHi
where fi is the average frequency (occurrences per second) of statei. Clearly
H
/0
/= mH
where m is the average number of symbols produced per second. H or H
/0
measures the amount of informa-
tion generated by the source per symbol or per second. If the logarithmic base is 2, they will represent bits
per symbol or per second.
If successive symbols are independent thenH is simply
/,
∑ pi log pi where pi is the probability of sym-
bol i. Suppose in this case we consider a long message of N symbols. It will contain with high probability
about p1N occurrences of the first symbol, p2N occurrences of the second, etc. Hence the probability of this
particular message will be roughly
p /= pp1N
1 pp2N
/#01/#01/#01 ppnN
n
or
log p
/:
/= N ∑
i
pi log pi
log p
/:
/= /, NH
H
/:
/=
log1 /= p
N
/:
H is thus approximately the logarithm of the reciprocal probability of a typical long sequence divided by the
number of symbols in the sequence. The same result holds for any source. Stated more precisely we have
(see Appendix 3):
Theorem 3: Given any /#0F/#3E 0 and /#0E/#3E 0, we can find an N0 such that the sequences of any lengthN /#15 N0
fall into two classes:
1. A set whose total probability is less than /#0F .
2. The remainder, all of whose members have probabilities satisfying the inequality
/#0C
/#0C
/#0C
/#0C
log p
/, 1
N
/, H
/#0C
/#0C
/#0C
/#0C
/#3C/#0E /:
In other words we are almost certain to have log p
/, 1
N very close to H when N is large.
A closely related result deals with the number of sequences of various probabilities. Consider again the
sequences of length N and let them be arranged in order of decreasing probability. We define n/#28 q/#29 to be
the number we must take from this set starting with the most probable one in order to accumulate a total
probability q for those taken.

Theorem 4:
Lim
N/! ∞
logn/#28 q/#29
N
/= H
when q does not equal 0 or 1.
We may interpret logn/#28 q/#29 as the number of bits required to specify the sequence when we consider only
the most probable sequences with a total probability q.T h e nlogn/#28 q/#29
N is the number of bits per symbol for
the specification. The theorem says that for large N this will be independent of q and equal to H.T h e r a t e
of growth of the logarithm of the number of reasonably probable sequences is given byH, regardless of our
interpretation of "reasonably probable." Due to these results, which are proved in Appendix 3, it is possible
for most purposes to treat the long sequences as though there were just 2HN of them, each with a probability
/, HN .
The next two theorems show that H and H
/0
can be determined by limiting operations directly from
the statistics of the message sequences, without reference to the states and transition probabilities between
states.
Theorem 5: Let p/#28 Bi
/#29 be the probability of a sequence Bi of symbols from the source. Let
GN
/= /,
N ∑
i
p/#28 Bi
/#29 log p/#28 Bi
/#29
where the sum is over all sequences Bi containing N symbols. Then GN is a monotonic decreasing function
of N and
Lim
N/! ∞
GN
/= H/:
Theorem 6: Let p/#28 Bi
/; Sj
/#29 be the probability of sequence Bi followed by symbol Sj and pBi
/#28 Sj
/#29/=
p/#28 Bi
/; Sj
/#29 /= p/#28 Bi
/#29 be the conditional probability of Sj after Bi.L e t
FN
/= /,
∑
i/; j
p/#28 Bi
/; Sj
/#29 log pBi
/#28 Sj
/#29
where the sum is over all blocks Bi of N /, 1 symbols and over all symbols Sj.T h e n FN is a monotonic
decreasing function of N,
FN
/= NGN
/, /#28 N /, 1/#29 GN/, 1
/;
GN
/=
N
N
∑
n/= 1
Fn
/;
FN
/#14 GN
/;
and LimN/! ∞ FN
/= H.
These results are derived in Appendix 3. They show that a series of approximations toH can be obtained
by considering only the statistical structure of the sequences extending over 1 /; 2/;/:/:/:/; N symbols. FN is the
better approximation. In fact FN is the entropy of the Nth order approximation to the source of the type
discussed above. If there are no statistical influences extending over more than N symbols, that is if the
conditional probability of the next symbol knowing the preceding/#28 N /, 1/#29 is not changed by a knowledge of
any before that, then FN
/= H. FN of course is the conditional entropy of the next symbol when the /#28 N /, 1/#29
preceding ones are known, while GN is the entropy per symbol of blocks of N symbols.
The ratio of the entropy of a source to the maximum value it could have while still restricted to the same
symbols will be called itsrelative entropy. This is the maximum compression possible when we encode into
the same alphabet. One minus the relative entropy is the redundancy. The redundancy of ordinary English,
not considering statistical structure over greater distances than about eight letters, is roughly 50%. This
means that when we write English half of what we write is determined by the structure of the language and
half is chosen freely. The figure 50% was found by several independent methods which all gave results in

this neighborhood. One is by calculation of the entropy of the approximations to English. A second method
is to delete a certain fraction of the letters from a sample of English text and then let someone attempt to
restore them. If they can be restored when 50% are deleted the redundancy must be greater than 50%. A
third method depends on certain known results in cryptography.
Two extremes of redundancy in English prose are represented by Basic English and by James Joyce's
book "Finnegans Wake". The Basic English vocabulary is limited to 850 words and the redundancy is very
high. This is reflected in the expansion that occurs when a passage is translated into Basic English. Joyce
on the other hand enlarges the vocabulary and is alleged to achieve a compression of semantic content.
The redundancy of a language is related to the existence of crossword puzzles. If the redundancy is
zero any sequence of letters is a reasonable text in the language and any two-dimensional array of letters
forms a crossword puzzle. If the redundancy is too high the language imposes too many constraints for large
crossword puzzles to be possible. A more detailed analysis shows that if we assume the constraints imposed
by the language are of a rather chaotic and random nature, large crossword puzzles are just possible when
the redundancy is 50%. If the redundancy is 33%, three-dimensional crossword puzzles should be possible,
etc.
8. R
EPRESENTATION OF THE ENCODING AND DECODING OPERATIONS
We have yet to represent mathematically the operations performed by the transmitter and receiver in en-
coding and decoding the information. Either of these will be called a discrete transducer. The input to the
transducer is a sequence of input symbols and its output a sequence of output symbols. The transducer may
have an internal memory so that its output depends not only on the present input symbol but also on the past
history. We assume that the internal memory is finite, i.e., there exist a finite number m of possible states of
the transducer and that its output is a function of the present state and the present input symbol. The next
state will be a second function of these two quantities. Thus a transducer can be described by two functions:
y
n
/= f /#28 xn
/;/#0B
n
/#29
/#0B
n/+ 1
/= g/#28 xn
/;/#0B
n
/#29
where
xn is the nth input symbol,
/#0B
n is the state of the transducer when the nth input symbol is introduced,
yn is the output symbol (or sequence of output symbols) produced when xn is introduced if the state is /#0B
n.
If the output symbols of one transducer can be identified with the input symbols of a second, they can be
connected in tandem and the result is also a transducer. If there exists a second transducer which operates
on the output of the first and recovers the original input, the first transducer will be called non-singular and
the second will be called its inverse.
Theorem 7: The output of a finite state transducer driven by a finite state statistical source is a finite
state statistical source, with entropy (per unit time) less than or equal to that of the input. If the transducer
is non-singular they are equal.
Let /#0B represent the state of the source, which produces a sequence of symbolsxi;a n dl e t/#0C be the state of
the transducer, which produces, in its output, blocks of symbolsyj. The combined system can be represented
by the "product state space" of pairs/#28 /#0B/; /#0C /#29 . Two points in the space /#28 /#0B
/;/#0C
/#29 and /#28 /#0B
/;/#0C
/#29 , are connected by
a line if /#0B
1 can produce an x which changes /#0C
1 to /#0C
2, and this line is given the probability of that x in this
case. The line is labeled with the block ofyj symbols produced by the transducer. The entropy of the output
can be calculated as the weighted sum over the states. If we sum first on/#0C each resulting term is less than or
equal to the corresponding term for /#0B , hence the entropy is not increased. If the transducer is non-singular
let its output be connected to the inverse transducer. IfH
/0
1, H
/0
2 and H
/0
3 are the output entropies of the source,
the first and second transducers respectively, then H
/0
/#15 H
/0
/#15 H
/0
/= H
/0
1 and therefore H
/0
/= H
/0
2.

Suppose we have a system of constraints on possible sequences of the type which can be represented by
a linear graph as in Fig. 2. If probabilities p
/#28 s/#29
ij were assigned to the various lines connecting statei to state j
this would become a source. There is one particular assignment which maximizes the resulting entropy (see
Appendix 4).
Theorem 8:
Let the system of constraints considered as a channel have a capacity C /= logW.I f w e
assign
p
/#28 s/#29
ij
/=
Bj
Bi
W
/, /`
/#28 s/#29
ij
where /`
/#28 s/#29
ij is the duration of the sth symbol leading from state i to state j and the Bi satisfy
Bi
/=
∑
s/; j
BjW
/, /`
/#28 s/#29
ij
then H is maximized and equal to C.
By proper assignment of the transition probabilities the entropy of symbols on a channel can be maxi-
mized at the channel capacity.
9. T HE FUNDAMENTAL THEOREM FOR A NOISELESS CHANNEL
We will now justify our interpretation of H as the rate of generating information by proving that H deter-
mines the channel capacity required with most efficient coding.
Theorem 9: Let a source have entropy H /#28 bits per symbol /#29 and a channel have a capacity C /#28 bits per
second/#29 . Then it is possible to encode the output of the source in such a way as to transmit at the average
rate C
H
/, /#0F symbols per second over the channel where /#0F is arbitrarily small. It is not possible to transmit at
an average rate greater than C
H .
The converse part of the theorem, that C
H cannot be exceeded, may be proved by noting that the entropy
of the channel input per second is equal to that of the source, since the transmitter must be non-singular, and
also this entropy cannot exceed the channel capacity. Hence H
/0
/#14 C and the number of symbols per second
/= H
/0
/= H /#14 C/= H.
The first part of the theorem will be proved in two different ways. The first method is to consider the
set of all sequences of N symbols produced by the source. For N large we can divide these into two groups,
one containing less than 2
/#28 H/+ /#11 /#29 N members and the second containing less than 2 RN members (where R is
the logarithm of the number of different symbols) and having a total probability less than/#16 .A s N increases
/#11 and /#16 approach zero. The number of signals of duration T in the channel is greater than 2
/#28 C/, /#12 /#29 T with /#12
small when T is large. if we choose
T /=
/#12
H
C
/+ /#15
/#13
N
then there will be a sufficient number of sequences of channel symbols for the high probability group when
N and T are sufficiently large (however small /#15 ) and also some additional ones. The high probability group
is coded in an arbitrary one-to-one way into this set. The remaining sequences are represented by larger
sequences, starting and ending with one of the sequences not used for the high probability group. This
special sequence acts as a start and stop signal for a different code. In between a sufficient time is allowed
to give enough different sequences for all the low probability messages. This will require
T
/=
/#12
R
C
/+ /'
/#13
N
where /' is small. The mean rate of transmission in message symbols per second will then be greater than
/#14
/#28 1 /, /#0E /#29
T
N
/+ /#0E
T1
N
/#23
/, 1
/=
/#14
/#28 1 /, /#0E /#29
/#10
H
C
/+ /#15
/#11
/+ /#0E
/#10
R
C
/+ /'
/#11
/#15
/, 1
/:

As N increases /#0E , /#15 and /' approach zero and the rate approaches C
H .
Another method of performing this coding and thereby proving the theorem can be described as follows:
Arrange the messages of length N in order of decreasing probability and suppose their probabilities are
p1
/#15 p2
/#15 p3
/#01/#01/#01 /#15 pn.L e tPs
/=
∑ s/, 1
1 pi;t h a ti sPs is the cumulative probability up to, but not including, ps.
We first encode into a binary system. The binary code for messages is obtained by expandingPs as a binary
number. The expansion is carried out to ms places, where ms is the integer satisfying:
log2
ps
/#14 ms
/#3C 1 /+ log2
ps
/:
Thus the messages of high probability are represented by short codes and those of low probability by long
codes. From these inequalities we have
2ms
/#14 ps
/#3C
2ms
/, 1
/:
The code for Ps will differ from all succeeding ones in one or more of its ms places, since all the remaining
Pi are at least 1
2ms larger and their binary expansions therefore differ in the first ms places. Consequently all
the codes are different and it is possible to recover the message from its code. If the channel sequences are
not already sequences of binary digits, they can be ascribed binary numbers in an arbitrary fashion and the
binary code thus translated into signals suitable for the channel.
The average number H
/0
of binary digits used per symbol of original message is easily estimated. We
have
H
/0
/=
N ∑ ms ps
/:
But,
N ∑
/#10
log2
ps
/#11
ps
/#14
N ∑ ms ps
/#3C
N ∑
/#10
1 /+ log2
ps
/#11
ps
and therefore,
GN
/#14 H
/0
/#3C GN
/+
N
As N increases GN approaches H, the entropy of the source and H
/0
approaches H.
We see from this that the inefficiency in coding, when only a finite delay of N symbols is used, need
not be greater than 1
N plus the difference between the true entropy H and the entropy GN calculated for
sequences of length N. The per cent excess time needed over the ideal is therefore less than
GN
H
/+
HN
/, 1/:
This method of encoding is substantially the same as one found independently by R. M. Fano. 9 His
method is to arrange the messages of lengthN in order of decreasing probability. Divide this series into two
groups of as nearly equal probability as possible. If the message is in the first group its first binary digit
will be 0, otherwise 1. The groups are similarly divided into subsets of nearly equal probability and the
particular subset determines the second binary digit. This process is continued until each subset contains
only one message. It is easily seen that apart from minor differences (generally in the last digit) this amounts
to the same thing as the arithmetic process described above.
10. D
ISCUSSION AND EXAMPLES
In order to obtain the maximum power transfer from a generator to a load, a transformer must in general be
introduced so that the generator as seen from the load has the load resistance. The situation here is roughly
analogous. The transducer which does the encoding should match the source to the channel in a statistical
sense. The source as seen from the channel through the transducer should have the same statistical structure
9Technical Report No. 65, The Research Laboratory of Electronics, M.I.T., March 17, 1949.

as the source which maximizes the entropy in the channel. The content of Theorem 9 is that, although an
exact match is not in general possible, we can approximate it as closely as desired. The ratio of the actual
rate of transmission to the capacity C may be called the efficiency of the coding system. This is of course
equal to the ratio of the actual entropy of the channel symbols to the maximum possible entropy.
In general, ideal or nearly ideal encoding requires a long delay in the transmitter and receiver. In the
noiseless case which we have been considering, the main function of this delay is to allow reasonably good
matching of probabilities to corresponding lengths of sequences. With a good code the logarithm of the
reciprocal probability of a long message must be proportional to the duration of the corresponding signal, in
fact
/#0C
/#0C
/#0C
log p
/, 1
T
/, C
/#0C
/#0C
/#0C
must be small for all but a small fraction of the long messages.
If a source can produce only one particular message its entropy is zero, and no channel is required. For
example, a computing machine set up to calculate the successive digits of /#19 produces a definite sequence
with no chance element. No channel is required to "transmit" this to another point. One could construct a
second machine to compute the same sequence at the point. However, this may be impractical. In such a case
we can choose to ignore some or all of the statistical knowledge we have of the source. We might consider
the digits of
/#19 to be a random sequence in that we construct a system capable of sending any sequence of
digits. In a similar way we may choose to use some of our statistical knowledge of English in constructing
a code, but not all of it. In such a case we consider the source with the maximum entropy subject to the
statistical conditions we wish to retain. The entropy of this source determines the channel capacity which
is necessary and sufficient. In the /#19 example the only information retained is that all the digits are chosen
from the set 0 /; 1/;/:/:/:/; 9. In the case of English one might wish to use the statistical saving possible due to
letter frequencies, but nothing else. The maximum entropy source is then the first approximation to English
and its entropy determines the required channel capacity.
As a simple example of some of these results consider a source which produces a sequence of letters
chosen from amongA, B, C, D with probabilities 1
2 , 1
4 , 1
8 , 1
8 , successive symbols being chosen independently.
We have
H /= /,
/,
2 log 1
/+
4 log 1
/+
8 log 1
/#01
/=
4 bits per symbol/:
Thus we can approximate a coding system to encode messages from this source into binary digits with an
average of 7
4 binary digit per symbol. In this case we can actually achieve the limiting value by the following
code (obtained by the method of the second proof of Theorem 9):
A 0
B 10
C 110
D 111
The average number of binary digits used in encoding a sequence ofN symbols will be
N
/,
/#02 1 /+
/#02 2 /+
/#02 3
/#01
/=
4 N/:
It is easily seen that the binary digits 0, 1 have probabilities 1
2 , 1
2 so the H for the coded sequences is one
bit per symbol. Since, on the average, we have 7
4 binary symbols per original letter, the entropies on a time
basis are the same. The maximum possible entropy for the original set is log4 /= 2, occurring when A, B, C,
D have probabilities 1
4 , 1
4 , 1
4 , 1
4 . Hence the relative entropy is 7
8 . We can translate the binary sequences into
the original set of symbols on a two-to-one basis by the following table:
00 A
/0
01 B
/0
10 C
/0
11 D
/0


## Part I — Discrete Noiseless Systems

This double process then encodes the original message into the same symbols but with an average compres-
sion ratio 7
8 .
As a second example consider a source which produces a sequence ofA's andB's with probabilityp for
A and q for B.I f p /#1C q we have
H /= /, log pp
/#28 1 /, p/#29
1/, p
/= /, plog p/#28 1 /, p/#29
/#28 1/, p/#29 /= p
/:
/= plog e
p
/:
In such a case one can construct a fairly good coding of the message on a 0, 1 channel by sending a special
sequence, say 0000, for the infrequent symbolA and then a sequence indicating thenumber of B's following
it. This could be indicated by the binary representation with all numbers containing the special sequence
deleted. All numbers up to 16 are represented as usual; 16 is represented by the next binary number after 16
which does not contain four zeros, namely 17 /= 10001, etc.
It can be shown that as p /! 0 the coding approaches ideal provided the length of the special sequence is
properly adjusted.
PART II: THE DISCRETE CHANNEL WITH NOISE
11. R EPRESENTATION OF A NOISY DISCRETE CHANNEL
We now consider the case where the signal is perturbed by noise during transmission or at one or the other
of the terminals. This means that the received signal is not necessarily the same as that sent out by the
transmitter. Two cases may be distinguished. If a particular transmitted signal always produces the same
received signal, i.e., the received signal is a definite function of the transmitted signal, then the effect may be
called distortion. If this function has an inverse --- no two transmitted signals producing the same received
signal --- distortion may be corrected, at least in principle, by merely performing the inverse functional
operation on the received signal.
The case of interest here is that in which the signal does not always undergo the same change in trans-
mission. In this case we may assume the received signal E to be a function of the transmitted signal S and a
second variable, the noise N.
E
/= f /#28 S/; N/#29
The noise is considered to be a chance variable just as the message was above. In general it may be repre-
sented by a suitable stochastic process. The most general type of noisy discrete channel we shall consider
is a generalization of the finite state noise-free channel described previously. We assume a finite number of
states and a set of probabilities
p
/#0B /; i
/#28 /#0C/; j/#29 /:
This is the probability, if the channel is in state/#0B and symbol i is transmitted, that symbol j will be received
and the channel left in state /#0C . Thus /#0B and /#0C range over the possible states, i over the possible transmitted
signals and j over the possible received signals. In the case where successive symbols are independently per-
turbed by the noise there is only one state, and the channel is described by the set of transition probabilities
pi
/#28 j/#29 , the probability of transmitted symbol i being received as j.
If a noisy channel is fed by a source there are two statistical processes at work: the source and the noise.
Thus there are a number of entropies that can be calculated. First there is the entropy H/#28 x/#29 of the source
or of the input to the channel (these will be equal if the transmitter is non-singular). The entropy of the
output of the channel, i.e., the received signal, will be denoted by H
/#28 y/#29 . In the noiseless case H/#28 y/#29/= H/#28 x/#29 .
The joint entropy of input and output will be H/#28 xy/#29 . Finally there are two conditional entropies Hx
/#28 y/#29 and
Hy
/#28 x/#29 , the entropy of the output when the input is known and conversely. Among these quantities we have
the relations
H/#28 x/; y/#29/= H/#28 x/#29/+ Hx
/#28 y/#29/= H/#28 y/#29/+ Hy
/#28 x/#29 /:
All of these entropies can be measured on a per-second or a per-symbol basis.

12. E QUIVOCATION AND CHANNEL CAPACITY
If the channel is noisy it is not in general possible to reconstruct the original message or the transmitted
signal with certainty by any operation on the received signal E. There are, however, ways of transmitting
the information which are optimal in combating noise. This is the problem which we now consider.
Suppose there are two possible symbols 0 and 1, and we are transmitting at a rate of 1000 symbols per
second with probabilities p0
/= p1
/=
2 . Thus our source is producing information at the rate of 1000 bits
per second. During transmission the noise introduces errors so that, on the average, 1 in 100 is received
incorrectly (a 0 as 1, or 1 as 0). What is the rate of transmission of information? Certainly less than 1000
bits per second since about 1% of the received symbols are incorrect. Our first impulse might be to say
the rate is 990 bits per second, merely subtracting the expected number of errors. This is not satisfactory
since it fails to take into account the recipient's lack of knowledge of where the errors occur. We may carry
it to an extreme case and suppose the noise so great that the received symbols are entirely independent of
the transmitted symbols. The probability of receiving 1 is
2 whatever was transmitted and similarly for 0.
Then about half of the received symbols are correct due to chance alone, and we would be giving the system
credit for transmitting 500 bits per second while actually no information is being transmitted at all. Equally
"good" transmission would be obtained by dispensing with the channel entirely and flipping a coin at the
receiving point.
Evidently the proper correction to apply to the amount of information transmitted is the amount of this
information which is missing in the received signal, or alternatively the uncertainty when we have received
a signal of what was actually sent. From our previous discussion of entropy as a measure of uncertainty it
seems reasonable to use the conditional entropy of the message, knowing the received signal, as a measure
of this missing information. This is indeed the proper definition, as we shall see later. Following this idea
the rate of actual transmission, R, would be obtained by subtracting from the rate of production (i.e., the
entropy of the source) the average rate of conditional entropy.
R
/= H/#28 x/#29 /, Hy
/#28 x/#29
The conditional entropy Hy
/#28 x/#29 will, for convenience, be called the equivocation. It measures the average
ambiguity of the received signal.
In the example considered above, if a 0 is received the a posteriori probability that a 0 was transmitted
is .99, and that a 1 was transmitted is .01. These figures are reversed if a 1 is received. Hence
Hy
/#28 x/#29/= /, /#5B /: 99log /: 99 /+ 0/: 01log0 /: 01/#5D
/= /: 081 bits/symbol
or 81 bits per second. We may say that the system is transmitting at a rate 1000/, 81 /= 919 bits per second.
In the extreme case where a 0 is equally likely to be received as a 0 or 1 and similarly for 1, thea posteriori
probabilities are 1
2 , 1
2 and
Hy
/#28 x/#29/= /,
/#02
2 log 1
/+
2 log 1
/#03
/= 1 bit per symbol
or 1000 bits per second. The rate of transmission is then 0 as it should be.
The following theorem gives a direct intuitive interpretation of the equivocation and also serves to justify
it as the unique appropriate measure. We consider a communication system and an observer (or auxiliary
device) who can see both what is sent and what is recovered (with errors due to noise). This observer notes
the errors in the recovered message and transmits data to the receiving point over a "correction channel" to
enable the receiver to correct the errors. The situation is indicated schematically in Fig. 8.
Theorem 10:
If the correction channel has a capacity equal to Hy
/#28 x/#29 it is possible to so encode the
correction data as to send it over this channel and correct all but an arbitrarily small fraction /#0F of the errors.
This is not possible if the channel capacity is less than Hy
/#28 x/#29 .

SOURCE
M
TRANSMI TTER RECEIVER CORRECTING
DEVICE
OBSERVER
M
/0
M
CORRECTION DA TA
Fig. 8---Schematic diagram of a correction system.
Roughly then, Hy
/#28 x/#29 is the amount of additional information that must be supplied per second at the
receiving point to correct the received message.
To prove the first part, consider long sequences of received message M
/0
and corresponding original
message M. There will be logarithmically THy
/#28 x/#29 of the M's which could reasonably have produced each
M
/0
. Thus we have THy
/#28 x/#29 binary digits to send each T seconds. This can be done with /#0F frequency of errors
on a channel of capacity Hy
/#28 x/#29 .
The second part can be proved by noting, first, that for any discrete chance variablesx, y, z
Hy
/#28 x/; z/#29 /#15 Hy
/#28 x/#29 /:
The left-hand side can be expanded to give
Hy
/#28 z/#29/+ Hyz
/#28 x/#29 /#15 Hy
/#28 x/#29
Hyz
/#28 x/#29 /#15 Hy
/#28 x/#29 /, Hy
/#28 z/#29 /#15 Hy
/#28 x/#29 /, H/#28 z/#29 /:
If we identifyx as the output of the source,y as the received signal andz as the signal sent over the correction
channel, then the right-hand side is the equivocation less the rate of transmission over the correction channel.
If the capacity of this channel is less than the equivocation the right-hand side will be greater than zero and
H
yz
/#28 x/#29 /#3E 0. But this is the uncertainty of what was sent, knowing both the received signal and the correction
signal. If this is greater than zero the frequency of errors cannot be arbitrarily small.
Example:
Suppose the errors occur at random in a sequence of binary digits: probability p that a digit is wrong
and q /= 1 /, p that it is right. These errors can be corrected if their position is known. Thus the
correction channel need only send information as to these positions. This amounts to transmitting
from a source which produces binary digits with probability p for 1 (incorrect) and q for 0 (correct).
This requires a channel of capacity
/, /#5B plog p /+ qlogq/#5D
which is the equivocation of the original system.
The rate of transmission R can be written in two other forms due to the identities noted above. We have
R /= H/#28 x/#29 /, Hy
/#28 x/#29
/= H/#28 y/#29 /, Hx
/#28 y/#29
/= H/#28 x/#29/+ H/#28 y/#29 /, H/#28 x/; y/#29 /:

The first defining expression has already been interpreted as the amount of information sent less the uncer-
tainty of what was sent. The second measures the amount received less the part of this which is due to noise.
The third is the sum of the two amounts less the joint entropy and therefore in a sense is the number of bits
per second common to the two. Thus all three expressions have a certain intuitive significance.
The capacity C of a noisy channel should be the maximum possible rate of transmission, i.e., the rate
when the source is properly matched to the channel. We therefore define the channel capacity by
C
/= Max
/,
H/#28 x/#29 /, Hy
/#28 x/#29
/#01
where the maximum is with respect to all possible information sources used as input to the channel. If the
channel is noiseless,Hy
/#28 x/#29/= 0. The definition is then equivalent to that already given for a noiseless channel
since the maximum entropy for the channel is its capacity.
13. T HE FUNDAMENTAL THEOREM FOR A DISCRETE CHANNEL WITH NOISE
It may seem surprising that we should define a definite capacity C for a noisy channel since we can never
send certain information in such a case. It is clear, however, that by sending the information in a redundant
form the probability of errors can be reduced. For example, by repeating the message many times and by a
statistical study of the different received versions of the message the probability of errors could be made very
small. One would expect, however, that to make this probability of errors approach zero, the redundancy
of the encoding must increase indefinitely, and the rate of transmission therefore approach zero. This is by
no means true. If it were, there would not be a very well defined capacity, but only a capacity for a given
frequency of errors, or a given equivocation; the capacity going down as the error requirements are made
more stringent. Actually the capacity C defined above has a very definite significance. It is possible to send
information at the rate C through the channel with as small a frequency of errors or equivocation as desired
by proper encoding. This statement is not true for any rate greater than C. If an attempt is made to transmit
at a higher rate thanC,s a yC
/+ R1, then there will necessarily be an equivocation equal to or greater than the
excess R1. Nature takes payment by requiring just that much uncertainty, so that we are not actually getting
any more than C through correctly.
The situation is indicated in Fig. 9. The rate of information into the channel is plotted horizontally and
the equivocation vertically. Any point above the heavy line in the shaded region can be attained and those
below cannot. The points on the line cannot in general be attained, but there will usually be two points on
the line that can.
These results are the main justification for the definition of C and will now be proved.
Theorem 11: Let a discrete channel have the capacityC and a discrete source the entropy per secondH.
If H /#14 C there exists a coding system such that the output of the source can be transmitted over the channel
with an arbitrarily small frequency of errors (or an arbitrarily small equivocation). If H /#3E C it is possible
to encode the source so that the equivocation is less than H /, C /+ /#0F where /#0F is arbitrarily small. There is no
method of encoding which gives an equivocation less thanH /, C.
The method of proving the first part of this theorem is not by exhibiting a coding method having the
desired properties, but by showing that such a code must exist in a certain group of codes. In fact we will
AT TAI NAB L E
REGION
C H/#28 x/#29
Hy
/#28 x/#29
SLOPE
=1 . 0
Fig. 9---The equivocation possible for a given input entropy to a channel.

average the frequency of errors over this group and show that this average can be made less than /#0F .I f t h e
average of a set of numbers is less than /#0F there must exist at least one in the set which is less than /#0F .T h i s
will establish the desired result.
The capacity C of a noisy channel has been defined as
C /= Max
/,
H/#28 x/#29 /, Hy
/#28 x/#29
/#01
where x is the input and y the output. The maximization is over all sources which might be used as input to
the channel.
Let S0 be a source which achieves the maximum capacity C. If this maximum is not actually achieved
by any source let S0 be a source which approximates to giving the maximum rate. Suppose S0 is used as
input to the channel. We consider the possible transmitted and received sequences of a long durationT .T h e
following will be true:
1. The transmitted sequences fall into two classes, a high probability group with about 2TH /#28 x/#29
members
and the remaining sequences of small total probability.
2. Similarly the received sequences have a high probability set of about 2 TH /#28 y/#29
members and a low
probability set of remaining sequences.
3. Each high probability output could be produced by about 2 THy
/#28 x/#29
inputs. The probability of all other
cases has a small total probability.
All the /#0F 's and /#0E 's implied by the words "small" and "about" in these statements approach zero as we
allow T to increase and S0 to approach the maximizing source.
The situation is summarized in Fig. 10 where the input sequences are points on the left and output
sequences points on the right. The fan of cross lines represents the range of possible causes for a typical
output.
M
E
2H/#28 x/#29 T
HIGH PROBABILITY
MESSAGES
2H/#28 y/#29 T
HIGH PROBABILITY
RECEIVED SIGNALS
2Hy
/#28 x/#29 T
REASONABLE CAUSES
FOR EACH E
2Hx
/#28 y/#29 T
REASONABLE EFFECTS
FOR EACH M
Fig. 10---Schematic representation of the relations between inputs and outputs in a channel.
Now suppose we have another source producing information at rate R with R /#3C C. In the period T this
source will have 2TR high probability messages. We wish to associate these with a selection of the possible
channel inputs in such a way as to get a small frequency of errors. We will set up this association in all

possible ways (using, however, only the high probability group of inputs as determined by the source S0)
and average the frequency of errors for this large class of possible coding systems. This is the same as
calculating the frequency of errors for a random association of the messages and channel inputs of duration
T . Suppose a particular output y
1 is observed. What is the probability of more than one message in the set
of possible causes of y1?T h e r ea r e2TR messages distributed at random in 2TH /#28 x/#29
points. The probability of
a particular point being a message is thus
2T /#28 R/, H/#28 x/#29/#29
/:
The probability that none of the points in the fan is a message (apart from the actual originating message) is
P /=
/#02
1 /, 2T/#28 R/, H/#28 x/#29/#29
/#03
2THy
/#28 x/#29
/:
Now R /#3C H/#28 x/#29 /, Hy
/#28 x/#29 so R /, H/#28 x/#29/= /, Hy
/#28 x/#29 /, /#11 with /#11 positive. Consequently
P /=
/#02
1 /, 2
/, THy
/#28 x/#29 /, T /#11
/#03
2THy
/#28 x/#29
approaches (as T /! ∞ )
1 /, 2
/, T/#11
/:
Hence the probability of an error approaches zero and the first part of the theorem is proved.
The second part of the theorem is easily shown by noting that we could merely send C bits per second
from the source, completely neglecting the remainder of the information generated. At the receiver the
neglected part gives an equivocation H
/#28 x/#29 /, C and the part transmitted need only add /#0F . This limit can also
be attained in many other ways, as will be shown when we consider the continuous case.
The last statement of the theorem is a simple consequence of our definition ofC. Suppose we can encode
a source with H/#28 x/#29/= C /+ a in such a way as to obtain an equivocation Hy
/#28 x/#29/= a /, /#0F with /#0F positive. Then
R /= H/#28 x/#29/= C /+ a and
H/#28 x/#29 /, Hy
/#28 x/#29/= C /+ /#0F
with /#0F positive. This contradicts the definition of C as the maximum of H/#28 x/#29 /, Hy
/#28 x/#29 .
Actually more has been proved than was stated in the theorem. If the average of a set of numbers is
within /#0F of of their maximum, a fraction of at most
p
/#0F can be more than
p
/#0F below the maximum. Since /#0F is
arbitrarily small we can say that almost all the systems are arbitrarily close to the ideal.
14. D ISCUSSION
The demonstration of Theorem 11, while not a pure existence proof, has some of the deficiencies of such
proofs. An attempt to obtain a good approximation to ideal coding by following the method of the proof is
generally impractical. In fact, apart from some rather trivial cases and certain limiting situations, no explicit
description of a series of approximation to the ideal has been found. Probably this is no accident but is
related to the difficulty of giving an explicit construction for a good approximation to a random sequence.
An approximation to the ideal would have the property that if the signal is altered in a reasonable way
by the noise, the original can still be recovered. In other words the alteration will not in general bring it
closer to another reasonable signal than the original. This is accomplished at the cost of a certain amount of
redundancy in the coding. The redundancy must be introduced in the proper way to combat the particular
noise structure involved. However, any redundancy in the source will usually help if it is utilized at the
receiving point. In particular, if the source already has a certain redundancy and no attempt is made to
eliminate it in matching to the channel, this redundancy will help combat noise. For example, in a noiseless
telegraph channel one could save about 50% in time by proper encoding of the messages. This is not done
and most of the redundancy of English remains in the channel symbols. This has the advantage, however,
of allowing considerable noise in the channel. A sizable fraction of the letters can be received incorrectly
and still reconstructed by the context. In fact this is probably not a bad approximation to the ideal in many
cases, since the statistical structure of English is rather involved and the reasonable English sequences are
not too far (in the sense required for the theorem) from a random selection.

As in the noiseless case a delay is generally required to approach the ideal encoding. It now has the
additional function of allowing a large sample of noise to affect the signal before any judgment is made
at the receiving point as to the original message. Increasing the sample size always sharpens the possible
statistical assertions.
The content of Theorem 11 and its proof can be formulated in a somewhat different way which exhibits
the connection with the noiseless case more clearly. Consider the possible signals of durationT and suppose
a subset of them is selected to be used. Let those in the subset all be used with equal probability, and suppose
the receiver is constructed to select, as the original signal, the most probable cause from the subset, when a
perturbed signal is received. We defineN
/#28 T/; q/#29 to be the maximum number of signals we can choose for the
subset such that the probability of an incorrect interpretation is less than or equal to q.
Theorem 12: Lim
T /! ∞
logN/#28 T/; q/#29
T
/= C,w h e r eC is the channel capacity, provided thatq does not equal 0 or
1.
In other words, no matter how we set out limits of reliability, we can distinguish reliably in time T
enough messages to correspond to aboutCT bits, when T is sufficiently large. Theorem 12 can be compared
with the definition of the capacity of a noiseless channel given in Section 1.
15. E XAMPLE OF A DISCRETE CHANNEL AND ITS CAPACITY
A simple example of a discrete channel is indicated in Fig. 11. There are three possible symbols. The first is
never affected by noise. The second and third each have probability p of coming through undisturbed, and
q of being changed into the other of the pair. We have (letting /#0B /= /, /#5B plog p /+ qlogq/#5D and P and Q be the
p
p
q
q
TRANSMI TTED
SYMBOLS
RECEIVED
SYMBOLS
Fig. 11---Example of a discrete channel.
probabilities of using the first and second symbols)
H/#28 x/#29/= /, PlogP /, 2QlogQ
Hy
/#28 x/#29/= 2Q/#0B/:
We wish to chooseP and Q in such a way as to maximizeH/#28 x/#29 /, Hy
/#28 x/#29 , subject to the constraintP/+ 2Q /= 1.
Hence we consider
U /= /, PlogP /, 2QlogQ /, 2Q/#0B /+ /#15 /#28 P /+ 2Q/#29
∂U
∂P
/= /, 1 /, logP /+ /#15 /= 0
∂U
∂Q
/= /, 2 /, 2log Q /, 2/#0B /+ 2/#15 /= 0/:
Eliminating /#15
logP /= logQ /+ /#0B
P /= Qe
/#0B
/= Q/#0C

P /=
/#0C
/#0C /+ 2 Q /=
/#0C /+ 2
/:
The channel capacity is then
C /= log
/#0C /+ 2
/#0C
/:
Note how this checks the obvious values in the cases p /= 1a n dp /=
2 .I nt h efi r s t ,/#0C /= 1a n dC /= log3,
which is correct since the channel is then noiseless with three possible symbols. If p /=
2 , /#0C /= 2a n d
C /= log2. Here the second and third symbols cannot be distinguished at all and act together like one
symbol. The first symbol is used with probability P /=
2 and the second and third together with probability
2 . This may be distributed between them in any desired way and still achieve the maximum capacity.
For intermediate values of p the channel capacity will lie between log2 and log3. The distinction
between the second and third symbols conveys some information but not as much as in the noiseless case.
The first symbol is used somewhat more frequently than the other two because of its freedom from noise.
16. T HE CHANNEL CAPACITY IN CERTAIN SPECIAL CASES
If the noise affects successive channel symbols independently it can be described by a set of transition
probabilities pij . This is the probability, if symbol i is sent, that j will be received. The maximum channel
rate is then given by the maximum of
/,
∑
i/; j
Pi pij log∑
i
Pi pij
/+
∑
i/; j
Pi pij log pij
w h e r ew ev a r yt h ePi subject to ∑ Pi
/= 1. This leads by the method of Lagrange to the equations,
∑
j
psj log psj
∑ i Pi pij
/= /#16 s /= 1/; 2/;/:/:/:/:
Multiplying by Ps and summing on s shows that /#16 /= C. Let the inverse of psj (if it exists) be hst so that
∑ s hst psj
/= /#0E
tj . Then:
∑
s/; j
hst psj log psj
/, log∑
i
Pi pit
/= C∑
s
hst
/:
Hence:
∑
i
Pi pit
/= exp
h
/, C ∑
s
hst
/+
∑
s/; j
hst psj log psj
i
or,
Pi
/=
∑
t
hit exp
h
/, C ∑
s
hst
/+
∑
s/; j
hst psj log psj
i
/:
This is the system of equations for determining the maximizing values ofPi, with C to be determined so
that ∑ Pi
/= 1. When this is done C will be the channel capacity, and the Pi the proper probabilities for the
channel symbols to achieve this capacity.
If each input symbol has the same set of probabilities on the lines emerging from it, and the same is true
of each output symbol, the capacity can be easily calculated. Examples are shown in Fig. 12. In such a case
Hx
/#28 y/#29 is independent of the distribution of probabilities on the input symbols, and is given by /,
∑ pi log pi
where the pi are the values of the transition probabilities from any input symbol. The channel capacity is
Max
/#02
H/#28 y/#29 /, Hx
/#28 y/#29
/#03
/= MaxH/#28 y/#29/+
∑ pi log pi
/:
The maximum ofH/#28 y/#29 is clearly logm where m is the number of output symbols, since it is possible to make
them all equally probable by making the input symbols equally probable. The channel capacity is therefore
C /= logm /+
∑ pi log pi
/:

a b c
/1/#2F/2
/1/#2F/2
/1/#2F/2
/1/#2F/2
/1/#2F/2
/1/#2F/2
/1/#2F/2
/1/#2F/2
/1/#2F/3
/1/#2F/3
/1/#2F/3
/1/#2F/3
/1/#2F/6
/1/#2F/6
/1/#2F/6
/1/#2F/6
/1/#2F/6
/1/#2F/6
/1/#2F/6
/1/#2F/3
/1/#2F/3
/1/#2F/3
/1/#2F/2
/1/#2F/2
/1/#2F/2
Fig. 12---Examples of discrete channels with the same transition probabilities for each input and for each output.
In Fig. 12a it would be
C /= log4 /, log2 /= log2 /:
This could be achieved by using only the 1st and 3d symbols. In Fig. 12b
C /= log4 /,
3 log3 /,
3 log6
/= log4 /, log3 /,
3 log2
/= log 1
3 2
/:
In Fig. 12c we have
C /= log3 /,
2 log2 /,
3 log3 /,
6 log6
/= log 3
2 3
3 6
/:
Suppose the symbols fall into several groups such that the noise never causes a symbol in one group to
be mistaken for a symbol in another group. Let the capacity for the nth group be Cn (in bits per second)
when we use only the symbols in this group. Then it is easily shown that, for best use of the entire set, the
total probability Pn of all symbols in the nth group should be
Pn
/=
2Cn
∑ 2Cn
/:
Within a group the probability is distributed just as it would be if these were the only symbols being used.
The channel capacity is
C /= log∑ 2Cn
/:
17. A N EXAMPLE OF EFFICIENT CODING
The following example, although somewhat unrealistic, is a case in which exact matching to a noisy channel
is possible. There are two channel symbols, 0 and 1, and the noise affects them in blocks of seven symbols.
A block of seven is either transmitted without error, or exactly one symbol of the seven is incorrect. These
eight possibilities are equally likely. We have
C
/= Max
/#02
H/#28 y/#29 /, Hx
/#28 y/#29
/#03
/=
/#02
7 /+
8 log 1
/#03
/=
7 bits/symbol/:
An efficient code, allowing complete correction of errors and transmitting at the rate C, is the following
(found by a method due to R. Hamming):


## Appendix

Let a block of seven symbols be X1
/; X2
/;/:/:/: /; X7.O f t h e s eX3, X5, X6 and X7 are message symbols and
chosen arbitrarily by the source. The other three are redundant and calculated as follows:
X4 is chosen to make /#0B /= X4
/+ X5
/+ X6
/+ X7 even
X2 """ " /#0C /= X2
/+ X3
/+ X6
/+ X7 "
X1 """ " /#0D /= X1
/+ X3
/+ X5
/+ X7 "
When a block of seven is received /#0B/; /#0C and /#0D are calculated and if even called zero, if odd called one. The
binary number /#0B/#0C /#0D then gives the subscript of the Xi that is incorrect (if 0 there was no error).
APPENDIX 1
THE GROWTH OF THE NUMBER OF BLOCKS OF SYMBOLS WITH A FINITE STATE CONDITION
Let Ni
/#28 L/#29 be the number of blocks of symbols of length L ending in state i.T h e nw eh a v e
Nj
/#28 L/#29/=
∑
i/; s
Ni
/,
L /, b
/#28 s/#29
ij
/#01
where b1
ij
/; b2
ij
/;/:/:/: /; bm
ij are the length of the symbols which may be chosen in statei and lead to state j.T h e s e
are linear difference equations and the behavior asL /! ∞ must be of the type
Nj
/= AjWL
/:
Substituting in the difference equation
AjW L
/=
∑
i/; s
AiWL/, b
/#28 s/#29
ij
or
Aj
/=
∑
i/; s
AiW
/, b
/#28 s/#29
ij
∑
i
/#10
∑
s
W
/, b
/#28 s/#29
ij
/, /#0E
ij
/#11
Ai
/= 0/:
For this to be possible the determinant
D/#28 W /#29/= j aij
j /=
/#0C
/#0C
/#0C
∑
s
W
/, b
/#28 s/#29
ij
/, /#0E
ij
/#0C
/#0C
/#0C
must vanish and this determines W, which is, of course, the largest real root of D /= 0.
The quantity C is then given by
C /= Lim
L/! ∞
log∑ AjWL
L
/= logW
and we also note that the same growth properties result if we require that all blocks start in the same (arbi-
trarily chosen) state.
APPENDIX 2
DERIV ATION OF H /= /,
∑ pi log pi
Let H
/#10
n
/;
n
/;/:/:/: /;
n
/#11
/= A/#28 n/#29 . From condition (3) we can decompose a choice from sm equally likely possi-
bilities into a series of m choices from s equally likely possibilities and obtain
A/#28 sm
/#29/= mA/#28 s/#29 /:


## Appendix

Similarly
A/#28 tn
/#29/= nA/#28 t/#29 /:
We can choose n arbitrarily large and find an m to satisfy
sm
/#14 tn
/#3C s
/#28 m/+ 1/#29
/:
Thus, taking logarithms and dividing by nlogs,
m
n
/#14
log t
log s
/#14
m
n
/+
n or
/#0C
/#0C
/#0C
m
n
/,
log t
log s
/#0C
/#0C
/#0C
/#3C/#0F
where /#0F is arbitrarily small. Now from the monotonic property of A/#28 n/#29 ,
A/#28 sm
/#29 /#14 A/#28 tn
/#29 /#14 A/#28 sm/+ 1
/#29
mA/#28 s/#29 /#14 nA/#28 t/#29 /#14 /#28 m /+ 1/#29 A/#28 s/#29 /:
Hence, dividing by nA/#28 s/#29 ,
m
n
/#14
A/#28 t/#29
A/#28 s/#29
/#14
m
n
/+
n or
/#0C
/#0C
/#0C
m
n
/,
A/#28 t/#29
A/#28 s/#29
/#0C
/#0C
/#0C
/#3C/#0F
/#0C
/#0C
/#0C
A/#28 t/#29
A/#28 s/#29
/,
logt
logs
/#0C
/#0C
/#0C
/#3C
2/#0F A/#28 t/#29/= K logt
where K must be positive to satisfy (2).
Now suppose we have a choice from n possibilities with commeasurable probabilities pi
/=
ni
∑ ni
where
the ni are integers. We can break down a choice from ∑ ni possibilities into a choice from n possibilities
with probabilities p1
/;/:/:/: /; pn and then, if the ith was chosen, a choice fromni with equal probabilities. Using
condition (3) again, we equate the total choice from ∑ ni as computed by two methods
K log∑ ni
/= H/#28 p1
/;/:/:/:/; pn
/#29/+ K ∑ pi logni
/:
Hence
H /= K
h
∑ pi log∑ ni
/,
∑ pi logni
i
/= /, K ∑ pi log ni
∑ ni
/= /, K ∑ pi log pi
/:
If the pi are incommeasurable, they may be approximated by rationals and the same expression must hold
by our continuity assumption. Thus the expression holds in general. The choice of coefficient K is a matter
of convenience and amounts to the choice of a unit of measure.
APPENDIX 3
THEOREMS ON ERGODIC SOURCES
If it is possible to go from any state with P /#3E 0 to any other along a path of probability p /#3E 0, the system is
ergodic and the strong law of large numbers can be applied. Thus the number of times a given path pij in
the network is traversed in a long sequence of length N is about proportional to the probability of being at
i,s a yPi, and then choosing this path, Pi pij N.I f N is large enough the probability of percentage error /#06 /#0E in
this is less than /#0F so that for all but a set of small probability the actual numbers lie within the limits
/#28 Pi pij
/#06 /#0E /#29 N/:
Hence nearly all sequences have a probability p given by
p /=
∏ p
/#28 Pi pij
/#06 /#0E /#29 N
ij


## Appendix

and log p
N is limited by
log p
N
/=
∑
/#28 Pi pij
/#06 /#0E /#29 log pij
or
/#0C
/#0C
/#0C
log p
N
/,
∑ Pi pij log pij
/#0C
/#0C
/#0C
/#3C/#11 /:
This proves Theorem 3.
Theorem 4 follows immediately from this on calculating upper and lower bounds for n/#28 q/#29 b a s e do nt h e
possible range of values of p in Theorem 3.
In the mixed (not ergodic) case if
L /=
∑ piLi
and the entropies of the components are H1
/#15 H2
/#15 /#01/#01/#01 /#15 Hn we have the
Theorem: Lim
N/! ∞
logn/#28 q/#29
N
/= /' /#28 q/#29 is a decreasing step function,
/' /#28 q/#29/= Hs in the interval
s/, 1
∑
/#0B
i
/#3C q /#3C
s
∑
/#0B
i
/:
To prove Theorems 5 and 6 first note that FN is monotonic decreasing because increasing N adds a
subscript to a conditional entropy. A simple substitution for pBi
/#28 Sj
/#29 in the definition of FN shows that
FN
/= NGN
/, /#28 N /, 1/#29 GN/, 1
and summing this for all N gives GN
/=
N ∑ Fn. Hence GN
/#15 FN and GN monotonic decreasing. Also they
must approach the same limit. By using Theorem 3 we see that Lim
N/! ∞
GN
/= H.
APPENDIX 4
MAXIMIZING THE RATE FOR A SYSTEM OF CONSTRAINTS
Suppose we have a set of constraints on sequences of symbols that is of the finite state type and can be
represented therefore by a linear graph. Let /`
/#28 s/#29
ij be the lengths of the various symbols that can occur in
passing from state i to state j. What distribution of probabilities Pi for the different states and p
/#28 s/#29
ij for
choosing symbol s in state i and going to state j maximizes the rate of generating information under these
constraints? The constraints define a discrete channel and the maximum rate must be less than or equal to
the capacity C of this channel, since if all blocks of large length were equally likely, this rate would result,
and if possible this would be best. We will show that this rate can be achieved by proper choice of thePi and
p
/#28 s/#29
ij .
The rate in question is
/,
∑ Pi p
/#28 s/#29
ij log p
/#28 s/#29
ij
∑ Pi p
/#28 s/#29
ij
/`
/#28 s/#29
ij
/=
N
M
/:
Let /`
ij
/=
∑ s
/`
/#28 s/#29
ij . Evidently for a maximum p
/#28 s/#29
ij
/= k exp/`
/#28 s/#29
ij . The constraints on maximization are ∑ Pi
/=
1, ∑ j pij
/= 1, ∑ Pi
/#28 pij
/, /#0E
ij
/#29/= 0. Hence we maximize
U /=
/,
∑ Pi pij log pij
∑ Pi pij
/`
ij
/+ /#15
∑
i
Pi
/+
∑
/#16
i pij
/+
∑
/#11
jPi
/#28 pij
/, /#0E
ij
/#29
∂U
∂pij
/= /,
MPi
/#28 1 /+ log pij
/#29/+ NPi
/`
ij
M2
/+ /#15 /+ /#16
i
/+ /#11
iPi
/= 0/:

Solving for pij
pij
/= AiBjD
/, /`
ij
/:
Since
∑
j
pij
/= 1/; A
/, 1
i
/=
∑
j
BjD
/, /`
ij
pij
/=
BjD
/, /`
ij
∑ s BsD
/, /`
is
/:
T h ec o r r e c tv a l u eo fD is the capacity C and the Bj are solutions of
Bi
/=
∑ BjC
/, /`
ij
for then
pij
/=
Bj
Bi
C
/, /`
ij
∑ Pi
Bj
Bi
C
/, /`
ij
/= Pj
or
∑
Pi
Bi
C
/, /`
ij
/=
Pj
Bj
/:
So that if /#15
i satisfy
∑
/#0D
iC
/, /`
ij
/= /#0D
j
Pi
/= Bi
/#0D
i
/:
Both the sets of equations for Bi and /#0D
i can be satisfied since C is such that
j C
/, /`
ij
/, /#0E
ij
j /= 0/:
In this case the rate is
/,
∑ Pi pij log Bj
Bi
C
/, /`
ij
∑ Pi pij
/`
ij
/= C /,
∑ Pi pij log Bj
Bi
∑ Pi pij
/`
ij
but
∑ Pi pij
/#28 logBj
/, logBi
/#29/=
∑
j
Pj logBj
/,
∑ Pi logBi
/= 0
Hence the rate isC and as this could never be exceeded this is the maximum, justifying the assumed solution.


## Part I — Discrete Noiseless Systems

PART III: MATHEMATICAL PRELIMINARIES
In this final installment of the paper we consider the case where the signals or the messages or both are
continuously variable, in contrast with the discrete nature assumed heretofore. To a considerable extent the
continuous case can be obtained through a limiting process from the discrete case by dividing the continuum
of messages and signals into a large but finite number of small regions and calculating the various parameters
involved on a discrete basis. As the size of the regions is decreased these parameters in general approach as
limits the proper values for the continuous case. There are, however, a few new effects that appear and also
a general change of emphasis in the direction of specialization of the general results to particular cases.
We will not attempt, in the continuous case, to obtain our results with the greatest generality, or with
the extreme rigor of pure mathematics, since this would involve a great deal of abstract measure theory
and would obscure the main thread of the analysis. A preliminary study, however, indicates that the theory
can be formulated in a completely axiomatic and rigorous manner which includes both the continuous and
discrete cases and many others. The occasional liberties taken with limiting processes in the present analysis
can be justified in all cases of practical interest.
18. S
ETS AND ENSEMBLES OF FUNCTIONS
We shall have to deal in the continuous case with sets of functions and ensembles of functions. A set of
functions, as the name implies, is merely a class or collection of functions, generally of one variable, time.
It can be specified by giving an explicit representation of the various functions in the set, or implicitly by
giving a property which functions in the set possess and others do not. Some examples are:
1. The set of functions:
f
/#12
/#28 t/#29/= sin/#28 t /+ /#12 /#29 /:
Each particular value of /#12 determines a particular function in the set.
2. The set of all functions of time containing no frequencies over W cycles per second.
3. The set of all functions limited in band to W and in amplitude to A.
4. The set of all English speech signals as functions of time.
An ensemble of functions is a set of functions together with a probability measure whereby we may
determine the probability of a function in the set having certain properties.1 For example with the set,
f
/#12
/#28 t/#29/= sin/#28 t /+ /#12 /#29 /;
we may give a probability distribution for /#12 , P/#28 /#12 /#29 . The set then becomes an ensemble.
Some further examples of ensembles of functions are:
1. A finite set of functions fk
/#28 t/#29 (k /= 1/; 2/;/:/:/:/; n) with the probability of fk being pk.
2. A finite dimensional family of functions
f /#28 /#0B
/;/#0B
/;/:/:/:/;/#0B
n;t/#29
with a probability distribution on the parameters /#0B
i:
p/#28 /#0B
/;/:/:/: /;/#0B
n
/#29 /:
For example we could consider the ensemble defined by
f /#28 a1
/;/:/:/:/; an
/;/#12
/;/:/:/: /;/#12
n;t/#29/=
n
∑
i/= 1
ai sini/#28 /! t /+ /#12
i
/#29
with the amplitudesai distributed normally and independently, and the phases/#12
i distributed uniformly
(from 0 to 2/#19 ) and independently.
1In mathematical terminology the functions belong to a measure space whose total measure is unity.

3. The ensemble
f /#28 ai
/; t/#29/=
/+ ∞
∑
n/= /, ∞
an
sin /#19 /#28 2Wt /, n/#29
/#19 /#28 2Wt /, n/#29
with the ai normal and independent all with the same standard deviation
p
N. This is a representation
of "white" noise, band limited to the band from 0 toW cycles per second and with average powerN.2
4. Let points be distributed on the t axis according to a Poisson distribution. At each selected point the
function f /#28 t/#29 is placed and the different functions added, giving the ensemble
∞
∑
k/= /, ∞
f /#28 t /+ tk
/#29
where the tk are the points of the Poisson distribution. This ensemble can be considered as a type of
impulse or shot noise where all the impulses are identical.
5. The set of English speech functions with the probability measure given by the frequency of occurrence
in ordinary use.
An ensemble of functions f
/#0B
/#28 t/#29 is stationary if the same ensemble results when all functions are shifted
any fixed amount in time. The ensemble
f
/#12
/#28 t/#29/= sin/#28 t /+ /#12 /#29
is stationary if /#12 is distributed uniformly from 0 to 2/#19 . If we shift each function by t1 we obtain
f
/#12
/#28 t /+ t1
/#29/= sin/#28 t /+ t1
/+ /#12 /#29
/= sin/#28 t /+ /' /#29
with /' distributed uniformly from 0 to 2 /#19 . Each function has changed but the ensemble as a whole is
invariant under the translation. The other examples given above are also stationary.
An ensemble is ergodic if it is stationary, and there is no subset of the functions in the set with a
probability different from 0 and 1 which is stationary. The ensemble
sin/#28 t /+ /#12 /#29
is ergodic. No subset of these functions of probability /6/= 0/; 1 is transformed into itself under all time trans-
lations. On the other hand the ensemble
asin/#28 t /+ /#12 /#29
with a distributed normally and /#12 uniform is stationary but not ergodic. The subset of these functions with
a between 0 and 1 for example is stationary.
Of the examples given, 3 and 4 are ergodic, and 5 may perhaps be considered so. If an ensemble is
ergodic we may say roughly that each function in the set is typical of the ensemble. More precisely it is
known that with an ergodic ensemble an average of any statistic over the ensemble is equal (with probability
1) to an average over the time translations of a particular function of the set.
3 Roughly speaking, each
function can be expected, as time progresses, to go through, with the proper frequency, all the convolutions
of any of the functions in the set.
2This representation can be used as a definition of band limited white noise. It has certain advantages in that it involves fewer
limiting operations than do definitions that have been used in the past. The name "white noise," already firmly entrenched in the
literature, is perhaps somewhat unfortunate. In optics white light means either any continuous spectrum as contrasted with a point
spectrum, or a spectrum which is flat with wavelength (which is not the same as a spectrum flat with frequency).
3This is the famous ergodic theorem or rather one aspect of this theorem which was proved in somewhat different formulations
by Birkoff, von Neumann, and Koopman, and subsequently generalized by Wiener, Hopf, Hurewicz and others. The literature on
ergodic theory is quite extensive and the reader is referred to the papers of these writers for precise and general formulations; e.g.,
E. Hopf, "Ergodentheorie,"Ergebnisse der Mathematik und ihrer Grenzgebiete,v. 5; "On Causality Statistics and Probability,"Journal
of Mathematics and Physics, v. XIII, No. 1, 1934; N. Wiener, "The Ergodic Theorem,"Duke Mathematical Journal, v. 5, 1939.

Just as we may perform various operations on numbers or functions to obtain new numbers or functions,
we can perform operations on ensembles to obtain new ensembles. Suppose, for example, we have an
ensemble of functions f
/#0B
/#28 t/#29 and an operator T which gives for each function f
/#0B
/#28 t/#29 a resulting function
g
/#0B
/#28 t/#29 :
g
/#0B
/#28 t/#29/= Tf
/#0B
/#28 t/#29 /:
Probability measure is defined for the setg
/#0B
/#28 t/#29 by means of that for the setf
/#0B
/#28 t/#29 . The probability of a certain
subset of the g
/#0B
/#28 t/#29 functions is equal to that of the subset of the f
/#0B
/#28 t/#29 functions which produce members of
the given subset of g functions under the operation T. Physically this corresponds to passing the ensemble
through some device, for example, a filter, a rectifier or a modulator. The output functions of the device
form the ensemble g
/#0B
/#28 t/#29 .
A device or operator T will be called invariant if shifting the input merely shifts the output, i.e., if
g
/#0B
/#28 t/#29/= Tf
/#0B
/#28 t/#29
implies
g
/#0B
/#28 t /+ t1
/#29/= Tf
/#0B
/#28 t /+ t1
/#29
for all f
/#0B
/#28 t/#29 and all t1. It is easily shown (see Appendix 5 that if T is invariant and the input ensemble is
stationary then the output ensemble is stationary. Likewise if the input is ergodic the output will also be
ergodic.
A filter or a rectifier is invariant under all time translations. The operation of modulation is not since the
carrier phase gives a certain time structure. However, modulation is invariant under all translations which
are multiples of the period of the carrier.
Wiener has pointed out the intimate relation between the invariance of physical devices under time
translations and Fourier theory.4 He has shown, in fact, that if a device is linear as well as invariant Fourier
analysis is then the appropriate mathematical tool for dealing with the problem.
An ensemble of functions is the appropriate mathematical representation of the messages produced by
a continuous source (for example, speech), of the signals produced by a transmitter, and of the perturbing
noise. Communication theory is properly concerned, as has been emphasized by Wiener, not with operations
on particular functions, but with operations on ensembles of functions. A communication system is designed
not for a particular speech function and still less for a sine wave, but for the ensemble of speech functions.
19. B AND LIMITED ENSEMBLES OF FUNCTIONS
If a function of time f /#28 t/#29 is limited to the band from 0 to W cycles per second it is completely determined
by giving its ordinates at a series of discrete points spaced 1
2W seconds apart in the manner indicated by the
following result.5
Theorem 13: Let f /#28 t/#29 contain no frequencies over W.T h e n
f /#28 t/#29/=
∞
∑
/, ∞
Xn
sin /#19 /#28 2Wt /, n/#29
/#19 /#28 2Wt /, n/#29
where
Xn
/= f
/#10
n
2W
/#11
/:
4Communication theory is heavily indebted to Wiener for much of its basic philosophy and theory. His classic NDRC report,
The Interpolation, Extrapolation and Smoothing of Stationary Time Series (Wiley, 1949), contains the first clear-cut formulation of
communication theory as a statistical problem, the study of operations on time series. This work, although chiefly concerned with the
linear prediction and filtering problem, is an important collateral reference in connection with the present paper. We may also refer
here to Wiener'sCybernetics (Wiley, 1948), dealing with the general problems of communication and control.
5For a proof of this theorem and further discussion see the author's paper "Communication in the Presence of Noise" published in
the Proceedings of the Institute of Radio Engineers,v. 37, No. 1, Jan., 1949, pp. 10--21.

In this expansion f /#28 t/#29 is represented as a sum of orthogonal functions. The coefficientsXn of the various
terms can be considered as coordinates in an infinite dimensional "function space." In this space each
function corresponds to precisely one point and each point to one function.
A function can be considered to be substantially limited to a time T if all the ordinates X
n outside this
interval of time are zero. In this case all but 2TW of the coordinates will be zero. Thus functions limited to
a band W and duration T correspond to points in a space of 2TW dimensions.
A subset of the functions of band W and duration T corresponds to a region in this space. For example,
the functions whose total energy is less than or equal toE correspond to points in a 2TW dimensional sphere
with radius r /=
p
2WE .
An ensemble of functions of limited duration and band will be represented by a probability distribution
p/#28 x1
/;/:/:/: /; xn
/#29 in the correspondingn dimensional space. If the ensemble is not limited in time we can consider
the 2TW coordinates in a given intervalT to represent substantially the part of the function in the intervalT
and the probability distribution p/#28 x1
/;/:/:/: /; xn
/#29 to give the statistical structure of the ensemble for intervals of
that duration.
20. E NTROPY OF A CONTINUOUS DISTRIBUTION
The entropy of a discrete set of probabilities p1
/;/:/:/: /; pn has been defined as:
H /= /,
∑ pi log pi
/:
In an analogous manner we define the entropy of a continuous distribution with the density distribution
function p/#28 x/#29 by:
H /= /,
Z
∞
/, ∞
p/#28 x/#29 log p/#28 x/#29 dx/:
With an n dimensional distribution p/#28 x1
/;/:/:/: /; xn
/#29 we have
H /= /,
Z
/#01/#01/#01
Z
p/#28 x1
/;/:/:/: /; xn
/#29 log p/#28 x1
/;/:/:/: /; xn
/#29 dx1
/#01/#01/#01 dxn
/:
If we have two arguments x and y (which may themselves be multidimensional) the joint and conditional
entropies of p/#28 x/; y/#29 are given by
H/#28 x/; y/#29/= /,
ZZ
p/#28 x/; y/#29 log p/#28 x/; y/#29 dxdy
and
Hx
/#28 y/#29/= /,
ZZ
p/#28 x/; y/#29 log p/#28 x/; y/#29
p/#28 x/#29
dxdy
Hy
/#28 x/#29/= /,
ZZ
p/#28 x/; y/#29 log p/#28 x/; y/#29
p/#28 y/#29
dxdy
where
p/#28 x/#29/=
Z
p/#28 x/; y/#29 dy
p/#28 y/#29/=
Z
p/#28 x/; y/#29 dx/:
The entropies of continuous distributions have most (but not all) of the properties of the discrete case.
In particular we have the following:
1. If x is limited to a certain volumev in its space, then H/#28 x/#29 is a maximum and equal to logv when p/#28 x/#29
is constant (1/= v)i nt h ev o l u m e .

2. With any two variables x, y we have
H/#28 x/; y/#29 /#14 H/#28 x/#29/+ H/#28 y/#29
with equality if (and only if) x and y are independent, i.e., p/#28 x/; y/#29/= p/#28 x/#29 p/#28 y/#29 (apart possibly from a
set of points of probability zero).
3. Consider a generalized averaging operation of the following type:
p
/0
/#28 y/#29/=
Z
a/#28 x/; y/#29 p/#28 x/#29 dx
with
Z
a/#28 x/; y/#29 dx /=
Z
a/#28 x/; y/#29 dy /= 1/; a/#28 x/; y/#29 /#15 0/:
Then the entropy of the averaged distribution p
/0
/#28 y/#29 is equal to or greater than that of the original
distribution p/#28 x/#29 .
4. We have
H/#28 x/; y/#29/= H/#28 x/#29/+ Hx
/#28 y/#29/= H/#28 y/#29/+ Hy
/#28 x/#29
and
Hx
/#28 y/#29 /#14 H/#28 y/#29 /:
5. Let p/#28 x/#29 be a one-dimensional distribution. The form ofp/#28 x/#29 giving a maximum entropy subject to the
condition that the standard deviation of x be fixed at /#1B is Gaussian. To show this we must maximize
H/#28 x/#29/= /,
Z
p/#28 x/#29 log p/#28 x/#29 dx
with
/#1B
/=
Z
p/#28 x/#29 x2 dx and 1 /=
Z
p/#28 x/#29 dx
as constraints. This requires, by the calculus of variations, maximizing
Z
/#02
/, p/#28 x/#29 log p/#28 x/#29/+ /#15 p/#28 x/#29 x2
/+ /#16 p/#28 x/#29
/#03
dx/:
The condition for this is
/, 1 /, log p/#28 x/#29/+ /#15 x2
/+ /#16 /= 0
and consequently (adjusting the constants to satisfy the constraints)
p/#28 x/#29/=
p
2/#19/#1B
e
/, /#28 x2
/= 2/#1B
/#29
/:
Similarly in n dimensions, suppose the second order moments of p/#28 x1
/;/:/:/: /; xn
/#29 are fixed at Aij :
Aij
/=
Z
/#01/#01/#01
Z
xixj p/#28 x1
/;/:/:/: /; xn
/#29 dx1
/#01/#01/#01 dxn
/:
Then the maximum entropy occurs (by a similar calculation) when p/#28 x1
/;/:/:/: /; xn
/#29 is the n dimensional
Gaussian distribution with the second order moments Aij .

6. The entropy of a one-dimensional Gaussian distribution whose standard deviation is /#1B is given by
H/#28 x/#29/= log
p
2/#19 e/#1B/:
This is calculated as follows:
p/#28 x/#29/=
p
2/#19/#1B
e
/, /#28 x2
/= 2/#1B
/#29
/, log p/#28 x/#29/= log
p
2/#19/#1B /+
x2
2/#1B
H/#28 x/#29/= /,
Z
p/#28 x/#29 log p/#28 x/#29 dx
/=
Z
p/#28 x/#29 log
p
2/#19/#1B dx /+
Z
p/#28 x/#29
x2
2/#1B
2 dx
/= log
p
2/#19/#1B /+
/#1B
2/#1B
/= log
p
2/#19/#1B /+ log
p
e
/= log
p
2/#19 e/#1B/:
Similarly the n dimensional Gaussian distribution with associated quadratic form aij is given by
p/#28 x1
/;/:/:/: /; xn
/#29/=
j aij
j
/#28 2/#19 /#29
n/= 2 exp
/#10
/,
2 ∑ aij xixj
/#11
and the entropy can be calculated as
H /= log/#28 2/#19 e/#29
n/= 2
j aij
j
/,
where j aij
j is the determinant whose elements are aij .
7. If x is limited to a half line (p/#28 x/#29/= 0f o rx /#14 0) and the first moment of x is fixed at a:
a /=
Z
∞
p/#28 x/#29 xdx /;
then the maximum entropy occurs when
p/#28 x/#29/=
ae
/, /#28 x/= a/#29
and is equal to logea.
8. There is one important difference between the continuous and discrete entropies. In the discrete case
the entropy measures in an absolute way the randomness of the chance variable. In the continuous
case the measurement is relative to the coordinate system. If we change coordinates the entropy will
in general change. In fact if we change to coordinates y1
/#01/#01/#01 yn the new entropy is given by
H/#28 y/#29/=
Z
/#01/#01/#01
Z
p/#28 x1
/;/:/:/: /; xn
/#29 J
/#10
x
y
/#11
log p/#28 x1
/;/:/:/: /; xn
/#29 J
/#10
x
y
/#11
dy1
/#01/#01/#01 dyn
where J
/,
x
y
/#01
is the Jacobian of the coordinate transformation. On expanding the logarithm and chang-
ing the variables to x1
/#01/#01/#01 xn, we obtain:
H/#28 y/#29/= H/#28 x/#29 /,
Z
/#01/#01/#01
Z
p/#28 x1
/;/:/:/: /; xn
/#29 logJ
/#10
x
y
/#11
dx1
/:/:/: dxn
/:

Thus the new entropy is the old entropy less the expected logarithm of the Jacobian. In the continuous
case the entropy can be considered a measure of randomnessrelative to an assumed standard, namely
the coordinate system chosen with each small volume element dx1
/#01/#01/#01 dxn given equal weight. When
we change the coordinate system the entropy in the new system measures the randomness when equal
volume elements dy1
/#01/#01/#01 dyn in the new system are given equal weight.
In spite of this dependence on the coordinate system the entropy concept is as important in the con-
tinuous case as the discrete case. This is due to the fact that the derived concepts of information rate
and channel capacity depend on the difference of two entropies and this difference does not depend
on the coordinate frame, each of the two terms being changed by the same amount.
The entropy of a continuous distribution can be negative. The scale of measurements sets an arbitrary
zero corresponding to a uniform distribution over a unit volume. A distribution which is more confined
than this has less entropy and will be negative. The rates and capacities will, however, always be non-
negative.
9. A particular case of changing coordinates is the linear transformation
y
j
/=
∑
i
aij xi
/:
In this case the Jacobian is simply the determinant j aij
j
/, 1 and
H/#28 y/#29/= H/#28 x/#29/+ logj aij
j /:
In the case of a rotation of coordinates (or any measure preserving transformation)J /= 1a n dH/#28 y/#29/=
H/#28 x/#29 .
21. E NTROPY OF AN ENSEMBLE OF FUNCTIONS
Consider an ergodic ensemble of functions limited to a certain band of widthW cycles per second. Let
p/#28 x1
/;/:/:/: /; xn
/#29
be the density distribution function for amplitudes x1
/;/:/:/: /; xn at n successive sample points. We define the
entropy of the ensemble per degree of freedom by
H
/0
/= /, Lim
n/! ∞
n
Z
/#01/#01/#01
Z
p/#28 x1
/;/:/:/:/; xn
/#29 log p/#28 x1
/;/:/:/: /; xn
/#29 dx1
/:/:/: dxn
/:
We may also define an entropy H per second by dividing, not by n, but by the time T in seconds for n
samples. Since n /= 2TW , H /= 2WH
/0
.
With white thermal noise p is Gaussian and we have
H
/0
/= log
p
2/#19 eN/;
H /= W log2 /#19 eN/:
For a given average power N, white noise has the maximum possible entropy. This follows from the
maximizing properties of the Gaussian distribution noted above.
The entropy for a continuous stochastic process has many properties analogous to that for discrete pro-
cesses. In the discrete case the entropy was related to the logarithm of the probability of long sequences,
and to the number of reasonably probable sequences of long length. In the continuous case it is related in
a similar fashion to the logarithm of the probability density for a long series of samples, and the volume of
reasonably high probability in the function space.
More precisely, if we assume p/#28 x1
/;/:/:/: /; xn
/#29 continuous in all the xi for all n, then for sufficiently large n
/#0C
/#0C
/#0C
log p
n
/, H
/0
/#0C
/#0C
/#0C
/#3C/#0F

for all choices of /#28 x1
/;/:/:/: /; xn
/#29 apart from a set whose total probability is less than /#0E , with /#0E and /#0F arbitrarily
small. This follows form the ergodic property if we divide the space into a large number of small cells.
The relation of H to volume can be stated as follows: Under the same assumptions consider the n
dimensional space corresponding to p/#28 x1
/;/:/:/: /; xn
/#29 .L e t Vn
/#28 q/#29 be the smallest volume in this space which
includes in its interior a total probability q.T h e n
Limn/! ∞
logVn
/#28 q/#29
n
/= H
/0
provided q does not equal 0 or 1.
These results show that for largen there is a rather well-defined volume (at least in the logarithmic sense)
of high probability, and that within this volume the probability density is relatively uniform (again in the
logarithmic sense).
In the white noise case the distribution function is given by
p/#28 x1
/;/:/:/: /; xn
/#29/=
/#28 2/#19 N/#29
n/= 2 exp/,
2N ∑ x2
i
/:
Since this depends only on ∑ x2
i the surfaces of equal probability density are spheres and the entire distri-
bution has spherical symmetry. The region of high probability is a sphere of radius
p
nN.A s n /! ∞ the
probability of being outside a sphere of radius
p
n/#28 N /+ /#0F /#29 approaches zero and 1
n times the logarithm of the
volume of the sphere approaches log
p
2/#19 eN.
In the continuous case it is convenient to work not with the entropyH of an ensemble but with a derived
quantity which we will call the entropy power. This is defined as the power in a white noise limited to the
same band as the original ensemble and having the same entropy. In other words if H
/0
is the entropy of an
ensemble its entropy power is
N1
/=
2/#19 e exp2H
/0
/:
In the geometrical picture this amounts to measuring the high probability volume by the squared radius of a
sphere having the same volume. Since white noise has the maximum entropy for a given power, the entropy
power of any noise is less than or equal to its actual power.
22. E NTROPY LOSS IN LINEAR FILTERS
Theorem 14: If an ensemble having an entropyH1 per degree of freedom in bandW is passed through a
filter with characteristic Y /#28 f /#29 the output ensemble has an entropy
H2
/= H1
/+
W
Z
W
log j Y /#28 f /#29 j
2 df /:
The operation of the filter is essentially a linear transformation of coordinates. If we think of the different
frequency components as the original coordinate system, the new frequency components are merely the old
ones multiplied by factors. The coordinate transformation matrix is thus essentially diagonalized in terms
of these coordinates. The Jacobian of the transformation is (for n sine and n cosine components)
J /=
n
∏
i/= 1
j Y /#28 fi
/#29 j
where the fi are equally spaced through the band W. This becomes in the limit
exp 1
W
Z
W
log j Y /#28 f /#29 j
2 df /:
Since J is constant its average value is the same quantity and applying the theorem on the change of entropy
with a change of coordinates, the result follows. We may also phrase it in terms of the entropy power. Thus
if the entropy power of the first ensemble is N1 that of the second is
N1 exp 1
W
Z
W
log j Y /#28 f /#29 j
2 df /:

TABLE I
ENTROPY ENTROPY
GAIN POWER POWER GAIN IMPULSE RESPONSE
FACTOR IN DECIBELS
/0 /1
/!
/1
1 /, /!
e2
/, 8/: 69 sin2
/#28 t/= 2/#29
t2
/= 2
/0 /1
/!
/1
1 /, /!
/#10
e
/#11
/, 5/: 33 2
/#14
sint
t3
/,
cost
t2
/#15
/0 /1
/!
/1
1 /, /!
0/: 411 /, 3/: 87 6
/#14
cost /, 1
t4
/,
cost
2t2
/+
sint
t3
/#15
/0 /1
/!
/1
p
1 /, /!
/#10
e
/#11
/, 2/: 67
/#19
J1
/#28 t/#29
t
/0 /1
/!
/1
/#0B
e2/#0B
/, 8/: 69/#0B
/#0B t2
/#02
cos/#28 1 /, /#0B /#29 t /, cost
/#03
The final entropy power is the initial entropy power multiplied by the geometric mean gain of the filter. If
the gain is measured in db, then the output entropy power will be increased by the arithmetic mean db gain
over W.
In Table I the entropy power loss has been calculated (and also expressed in db) for a number of ideal
gain characteristics. The impulsive responses of these filters are also given forW /= 2/#19 , with phase assumed
to be 0.
The entropy loss for many other cases can be obtained from these results. For example the entropy
power factor 1/= e2 for the first case also applies to any gain characteristic obtain from 1 /, /! by a measure
preserving transformation of the /! axis. In particular a linearly increasing gain G/#28 /! /#29/= /! , or a "saw tooth"
characteristic between 0 and 1 have the same entropy loss. The reciprocal gain has the reciprocal factor.
Thus 1/=/! has the factor e2. Raising the gain to any power raises the factor to this power.
23. E NTROPY OF A SUM OF TWO ENSEMBLES
If we have two ensembles of functions f
/#0B
/#28 t/#29 and g
/#0C
/#28 t/#29 we can form a new ensemble by "addition." Suppose
the first ensemble has the probability density function p/#28 x1
/;/:/:/: /; xn
/#29 and the second q/#28 x1
/;/:/:/: /; xn
/#29 . Then the


## Part I — Discrete Noiseless Systems

density function for the sum is given by the convolution:
r/#28 x1
/;/:/:/: /; xn
/#29/=
Z
/#01/#01/#01
Z
p/#28 y1
/;/:/:/: /; yn
/#29 q/#28 x1
/, y1
/;/:/:/: /; xn
/, yn
/#29 dy1
/#01/#01/#01 dyn
/:
Physically this corresponds to adding the noises or signals represented by the original ensembles of func-
tions.
The following result is derived in Appendix 6.
Theorem 15: Let the average power of two ensembles be N1 and N2 and let their entropy powers be N1
and N2. Then the entropy power of the sum, N3, is bounded by
N1
/+ N2
/#14 N3
/#14 N1
/+ N2
/:
White Gaussian noise has the peculiar property that it can absorb any other noise or signal ensemble
which may be added to it with a resultant entropy power approximately equal to the sum of the white noise
power and the signal power (measured from the average signal value, which is normally zero), provided the
signal power is small, in a certain sense, compared to noise.
Consider the function space associated with these ensembles having n dimensions. The white noise
corresponds to the spherical Gaussian distribution in this space. The signal ensemble corresponds to another
probability distribution, not necessarily Gaussian or spherical. Let the second moments of this distribution
about its center of gravity be a
ij .T h a ti s ,i fp/#28 x1
/;/:/:/: /; xn
/#29 is the density distribution function
aij
/=
Z
/#01/#01/#01
Z
p/#28 xi
/, /#0B
i
/#29/#28 xj
/, /#0B
j
/#29 dx1
/#01/#01/#01 dxn
where the /#0B
i are the coordinates of the center of gravity. Now aij is a positive definite quadratic form, and
we can rotate our coordinate system to align it with the principal directions of this form. aij is then reduced
to diagonal form bii. We require that each bii be small compared to N, the squared radius of the spherical
distribution.
In this case the convolution of the noise and signal produce approximately a Gaussian distribution whose
corresponding quadratic form is
N /+ bii
/:
The entropy power of this distribution is
h
∏
/#28 N /+ bii
/#29
i
1/= n
or approximately
/=
h
/#28 N/#29
n
/+
∑ bii
/#28 N/#29
n/, 1
i
1/= n
/:
/= N /+
n ∑ bii
/:
The last term is the signal power, while the first is the noise power.
PART IV: THE CONTINUOUS CHANNEL
24. T HE CAPACITY OF A CONTINUOUS CHANNEL
In a continuous channel the input or transmitted signals will be continuous functions of timef /#28 t/#29 belonging
to a certain set, and the output or received signals will be perturbed versions of these. We will consider
only the case where both transmitted and received signals are limited to a certain band W . They can then
be specified, for a time T ,b y2 TW numbers, and their statistical structure by finite dimensional distribution
functions. Thus the statistics of the transmitted signal will be determined by
P/#28 x1
/;/:/:/: /; xn
/#29/= P/#28 x/#29

and those of the noise by the conditional probability distribution
Px1
/;/:/:/:/; xn
/#28 y1
/;/:/:/: /; yn
/#29/= Px
/#28 y/#29 /:
The rate of transmission of information for a continuous channel is defined in a way analogous to that
for a discrete channel, namely
R /= H/#28 x/#29 /, Hy
/#28 x/#29
where H/#28 x/#29 is the entropy of the input and Hy
/#28 x/#29 the equivocation. The channel capacity C is defined as the
maximum of R when we vary the input over all possible ensembles. This means that in a finite dimensional
approximation we must vary P/#28 x/#29/= P/#28 x1
/;/:/:/: /; xn
/#29 and maximize
/,
Z
P/#28 x/#29 logP/#28 x/#29 dx /+
ZZ
P/#28 x/; y/#29 log P/#28 x/; y/#29
P/#28 y/#29
dxdy /:
This can be written
ZZ
P/#28 x/; y/#29 log P/#28 x/; y/#29
P/#28 x/#29 P/#28 y/#29
dxdy
using the fact that
ZZ
P/#28 x/; y/#29 logP/#28 x/#29 dxdy /=
Z
P/#28 x/#29 logP/#28 x/#29 dx. The channel capacity is thus expressed as
follows:
C /= Lim
T /! ∞
Max
P/#28 x/#29
T
ZZ
P/#28 x/; y/#29 log P/#28 x/; y/#29
P/#28 x/#29 P/#28 y/#29
dxdy /:
It is obvious in this form that R and C are independent of the coordinate system since the numerator
and denominator in log P/#28 x/; y/#29
P/#28 x/#29 P/#28 y/#29
will be multiplied by the same factors when x and y are transformed in
any one-to-one way. This integral expression forC is more general than H/#28 x/#29 /, Hy
/#28 x/#29 . Properly interpreted
(see Appendix 7) it will always exist whileH/#28 x/#29 /, Hy
/#28 x/#29 may assume an indeterminate form ∞ /, ∞ in some
cases. This occurs, for example, if x is limited to a surface of fewer dimensions than n in its n dimensional
approximation.
If the logarithmic base used in computing H/#28 x/#29 and Hy
/#28 x/#29 is two then C is the maximum number of
binary digits that can be sent per second over the channel with arbitrarily small equivocation, just as in
the discrete case. This can be seen physically by dividing the space of signals into a large number of
small cells, sufficiently small so that the probability density Px
/#28 y/#29 of signal x being perturbed to point y is
substantially constant over a cell (either ofx or y). If the cells are considered as distinct points the situation is
essentially the same as a discrete channel and the proofs used there will apply. But it is clear physically that
this quantizing of the volume into individual points cannot in any practical situation alter the final answer
significantly, provided the regions are sufficiently small. Thus the capacity will be the limit of the capacities
for the discrete subdivisions and this is just the continuous capacity defined above.
On the mathematical side it can be shown first (see Appendix 7) that if u is the message, x is the signal,
y is the received signal (perturbed by noise) and v is the recovered message then
H
/#28 x/#29 /, Hy
/#28 x/#29 /#15 H/#28 u/#29 /, Hv
/#28 u/#29
regardless of what operations are performed on u to obtain x or on y to obtain v. Thus no matter how we
encode the binary digits to obtain the signal, or how we decode the received signal to recover the message,
the discrete rate for the binary digits does not exceed the channel capacity we have defined. On the other
hand, it is possible under very general conditions to find a coding system for transmitting binary digits at the
rate C with as small an equivocation or frequency of errors as desired. This is true, for example, if, when we
take a finite dimensional approximating space for the signal functions, P
/#28 x/; y/#29 is continuous in both x and y
except at a set of points of probability zero.
An important special case occurs when the noise is added to the signal and is independent of it (in the
probability sense). Then Px
/#28 y/#29 is a function only of the difference n /=/#28 y /, x/#29 ,
Px
/#28 y/#29/= Q/#28 y /, x/#29

and we can assign a definite entropy to the noise (independent of the statistics of the signal), namely the
entropy of the distribution Q/#28 n/#29 . This entropy will be denoted by H/#28 n/#29 .
Theorem 16: If the signal and noise are independent and the received signal is the sum of the transmitted
signal and the noise then the rate of transmission is
R /= H/#28 y/#29 /, H/#28 n/#29 /;
i.e., the entropy of the received signal less the entropy of the noise. The channel capacity is
C /= Max
P/#28 x/#29
H/#28 y/#29 /, H/#28 n/#29 /:
We have, sincey /= x /+ n:
H/#28 x/; y/#29/= H/#28 x/; n/#29 /:
Expanding the left side and using the fact that x and n are independent
H/#28 y/#29/+ Hy
/#28 x/#29/= H/#28 x/#29/+ H/#28 n/#29 /:
Hence
R /= H/#28 x/#29 /, Hy
/#28 x/#29/= H/#28 y/#29 /, H/#28 n/#29 /:
Since H/#28 n/#29 is independent of P/#28 x/#29 , maximizing R requires maximizing H/#28 y/#29 , the entropy of the received
signal. If there are certain constraints on the ensemble of transmitted signals, the entropy of the received
signal must be maximized subject to these constraints.
25. C HANNEL CAPACITY WITH AN AVERAGE POWER LIMITATION
A simple application of Theorem 16 is the case when the noise is a white thermal noise and the transmitted
signals are limited to a certain average power P. Then the received signals have an average power P /+ N
where N is the average noise power. The maximum entropy for the received signals occurs when they also
form a white noise ensemble since this is the greatest possible entropy for a powerP/+ N and can be obtained
by a suitable choice of transmitted signals, namely if they form a white noise ensemble of power P.T h e
entropy (per second) of the received ensemble is then
H/#28 y/#29/= W log2 /#19 e/#28 P /+ N/#29 /;
and the noise entropy is
H/#28 n/#29/= W log2 /#19 eN/:
The channel capacity is
C /= H/#28 y/#29 /, H/#28 n/#29/= W log P /+ N
N
/:
Summarizing we have the following:
Theorem 17: The capacity of a channel of band W perturbed by white thermal noise power N when the
average transmitter power is limited to P is given by
C /= W log P /+ N
N
/:
This means that by sufficiently involved encoding systems we can transmit binary digits at the rate
W log2
P /+ N
N bits per second, with arbitrarily small frequency of errors. It is not possible to transmit at a
higher rate by any encoding system without a definite positive frequency of errors.
To approximate this limiting rate of transmission the transmitted signals must approximate, in statistical
properties, a white noise. 6 A system which approaches the ideal rate may be described as follows: Let
6This and other properties of the white noise case are discussed from the geometrical point of view in "Communication in the
Presence of Noise,"loc. cit.

M /= 2s samples of white noise be constructed each of duration T . These are assigned binary numbers from
0t o M /, 1. At the transmitter the message sequences are broken up into groups of s and for each group
the corresponding noise sample is transmitted as the signal. At the receiver the M samples are known and
the actual received signal (perturbed by noise) is compared with each of them. The sample which has the
least R.M.S. discrepancy from the received signal is chosen as the transmitted signal and the corresponding
binary number reconstructed. This process amounts to choosing the most probable ( a posteriori) signal.
The number M of noise samples used will depend on the tolerable frequency
/#0F of errors, but for almost all
selections of samples we have
Lim
/#0F /! 0
Lim
T /! ∞
logM/#28 /#0F/; T /#29
T
/= W log P /+ N
N
/;
so that no matter how small /#0F is chosen, we can, by taking T sufficiently large, transmit as near as we wish
to TW log P /+ N
N binary digits in the time T .
Formulas similar to C /= W log P /+ N
N for the white noise case have been developed independently
by several other writers, although with somewhat different interpretations. We may mention the work of
N. Wiener,7 W. G. Tuller,8 and H. Sullivan in this connection.
In the case of an arbitrary perturbing noise (not necessarily white thermal noise) it does not appear that
the maximizing problem involved in determining the channel capacityC can be solved explicitly. However,
upper and lower bounds can be set forC in terms of the average noise powerN the noise entropy power N1.
These bounds are sufficiently close together in most practical cases to furnish a satisfactory solution to the
problem.
Theorem 18: The capacity of a channel of band W perturbed by an arbitrary noise is bounded by the
inequalities
W log P /+ N1
N1
/#14 C /#14 W log P /+ N
N1
where
P /= average transmitter power
N /= average noise power
N1
/= entropy power of the noise.
Here again the average power of the perturbed signals will be P /+ N. The maximum entropy for this
power would occur if the received signal were white noise and would be W log2 /#19 e/#28 P /+ N/#29 . It may not
be possible to achieve this; i.e., there may not be any ensemble of transmitted signals which, added to the
perturbing noise, produce a white thermal noise at the receiver, but at least this sets an upper bound toH/#28 y/#29 .
We have, therefore
C /= MaxH/#28 y/#29 /, H/#28 n/#29
/#14 W log2 /#19 e/#28 P /+ N/#29 /, W log2 /#19 eN1
/:
This is the upper limit given in the theorem. The lower limit can be obtained by considering the rate if we
make the transmitted signal a white noise, of power P. In this case the entropy power of the received signal
must be at least as great as that of a white noise of power P /+ N1 since we have shown in in a previous
theorem that the entropy power of the sum of two ensembles is greater than or equal to the sum of the
individual entropy powers. Hence
MaxH/#28 y/#29 /#15 W log2 /#19 e/#28 P /+ N1
/#29
7Cybernetics, loc. cit.
8"Theoretical Limitations on the Rate of Transmission of Information," Proceedings of the Institute of Radio Engineers, v. 37,
No. 5, May, 1949, pp. 468--78.

and
C /#15 W log2 /#19 e/#28 P /+ N1
/#29 /, W log2 /#19 eN1
/= W log P /+ N1
N1
/:
As P increases, the upper and lower bounds approach each other, so we have as an asymptotic rate
W log P /+ N
N1
/:
If the noise is itself white, N /= N1 and the result reduces to the formula proved previously:
C /= W log
/#10
1 /+
P
N
/#11
/:
If the noise is Gaussian but with a spectrum which is not necessarily flat, N1 is the geometric mean of
the noise power over the various frequencies in the bandW. Thus
N1
/= exp 1
W
Z
W
logN/#28 f /#29 df
where N/#28 f /#29 is the noise power at frequency f .
Theorem 19: If we set the capacity for a given transmitter powerP equal to
C /= W log P /+ N /, /#11
N1
then /#11 is monotonic decreasing as P increases and approaches 0 as a limit.
Suppose that for a given power P1 the channel capacity is
W log P1
/+ N /, /#11
N1
/:
This means that the best signal distribution, say p/#28 x/#29 , when added to the noise distribution q/#28 x/#29 , gives a
received distribution r/#28 y/#29 whose entropy power is /#28 P1
/+ N /, /#11
/#29 . Let us increase the power to P1
/+ /#01 P by
adding a white noise of power /#01 P to the signal. The entropy of the received signal is now at least
H/#28 y/#29/= W log2 /#19 e/#28 P1
/+ N /, /#11
/+ /#01 P/#29
by application of the theorem on the minimum entropy power of a sum. Hence, since we can attain the
H indicated, the entropy of the maximizing distribution must be at least as great and /#11 must be monotonic
decreasing. To show that /#11 /! 0a s P /! ∞ consider a signal which is white noise with a large P.W h a t e v e r
the perturbing noise, the received signal will be approximately a white noise, ifP is sufficiently large, in the
sense of having an entropy power approaching P /+ N.
26. T HE CHANNEL CAPACITY WITH A PEAK POWER LIMITATION
In some applications the transmitter is limited not by the average power output but by the peak instantaneous
power. The problem of calculating the channel capacity is then that of maximizing (by variation of the
ensemble of transmitted symbols)
H/#28 y/#29 /, H/#28 n/#29
subject to the constraint that all the functions f /#28 t/#29 in the ensemble be less than or equal to
p
S, say, for all
t. A constraint of this type does not work out as well mathematically as the average power limitation. The
most we have obtained for this case is a lower bound valid for all S
N , an "asymptotic" upper bound (valid
for large S
N ) and an asymptotic value of C for S
N small.

Theorem 20: The channel capacity C for a band W perturbed by white thermal noise of power N is
bounded by
C /#15 W log 2
/#19 e3
S
N
/;
where S is the peak allowed transmitter power. For sufficiently large S
N
C /#14 W log
/#19 e S /+ N
N
/#28 1 /+ /#0F /#29
where /#0F is arbitrarily small. As S
N
/! 0 (and provided the band W starts at 0)
C
/.
W log
/#12
1 /+
S
N
/#13
/! 1/:
We wish to maximize the entropy of the received signal. If S
N is large this will occur very nearly when
we maximize the entropy of the transmitted ensemble.
The asymptotic upper bound is obtained by relaxing the conditions on the ensemble. Let us suppose that
the power is limited toS not at every instant of time, but only at the sample points. The maximum entropy of
the transmitted ensemble under these weakened conditions is certainly greater than or equal to that under the
original conditions. This altered problem can be solved easily. The maximum entropy occurs if the different
samples are independent and have a distribution function which is constant from/,
p
S to /+
p
S. The entropy
can be calculated as
W log4S/:
The received signal will then have an entropy less than
W log/#28 4S /+ 2/#19 eN/#29/#28 1 /+ /#0F /#29
with /#0F /! 0a s S
N
/! ∞ and the channel capacity is obtained by subtracting the entropy of the white noise,
W log2 /#19 eN:
W log/#28 4S /+ 2/#19 eN/#29/#28 1 /+ /#0F /#29 /, W log/#28 2/#19 eN/#29/= W log
/#19 e S /+ N
N
/#28 1 /+ /#0F /#29 /:
This is the desired upper bound to the channel capacity.
To obtain a lower bound consider the same ensemble of functions. Let these functions be passed through
an ideal filter with a triangular transfer characteristic. The gain is to be unity at frequency 0 and decline
linearly down to gain 0 at frequency W . We first show that the output functions of the filter have a peak
power limitation S at all times (not just the sample points). First we note that a pulse sin2 /#19 Wt
2/#19 Wt going into
the filter produces
sin2
/#19 Wt
/#28 /#19 Wt /#29
in the output. This function is never negative. The input function (in the general case) can be thought of as
the sum of a series of shifted functions
asin2 /#19 Wt
2/#19 Wt
where a, the amplitude of the sample, is not greater than
p
S. Hence the output is the sum of shifted functions
of the non-negative form above with the same coefficients. These functions being non-negative, the greatest
positive value for anyt is obtained when all the coefficients a have their maximum positive values, i.e.,
p
S.
In this case the input function was a constant of amplitude
p
S and since the filter has unit gain for D.C., the
output is the same. Hence the output ensemble has a peak power S.


## Part V — The Rate for a Continuous Source

The entropy of the output ensemble can be calculated from that of the input ensemble by using the
theorem dealing with such a situation. The output entropy is equal to the input entropy plus the geometrical
mean gain of the filter:
Z
W
logG2 df /=
Z
W
log
/#10
W /, f
W
/#11
df /= /, 2W/:
Hence the output entropy is
W log4S /, 2W /= W log 4S
e2
and the channel capacity is greater than
W log 2
/#19 e3
S
N
/:
We now wish to show that, for smallS
N (peak signal power over average white noise power), the channel
capacity is approximately
C /= W log
/#12
1 /+
S
N
/#13
/:
More precisely C
/.
W log
/#12
1 /+
S
N
/#13
/! 1a s S
N
/! 0. Since the average signal power P is less than or equal
to the peak S, it follows that for all S
N
C /#14 W log
/#12
1 /+
P
N
/#13
/#14 W log
/#12
1 /+
S
N
/#13
/:
Therefore, if we can find an ensemble of functions such that they correspond to a rate nearlyW log
/#12
1 /+
S
N
/#13
and are limited to band W and peak S the result will be proved. Consider the ensemble of functions of the
following type. A series oft samples have the same value, either/+
p
S or /,
p
S, then the nextt samples have
the same value, etc. The value for a series is chosen at random, probability 1
2 for /+
p
S and 1
2 for /,
p
S.I f
this ensemble be passed through a filter with triangular gain characteristic (unit gain at D.C.), the output is
peak limited to
/#06 S. Furthermore the average power is nearlyS and can be made to approach this by takingt
sufficiently large. The entropy of the sum of this and the thermal noise can be found by applying the theorem
on the sum of a noise and a small signal. This theorem will apply if
p
t S
N
is sufficiently small. This can be ensured by taking S
N small enough (after t is chosen). The entropy power
will be S /+ N to as close an approximation as desired, and hence the rate of transmission as near as we wish
to
W log
/#12
S /+ N
N
/#13
/:
PART V: THE RATE FOR A CONTINUOUS SOURCE
27. F IDELITY EVA L UAT I O NFUNCTIONS
In the case of a discrete source of information we were able to determine a definite rate of generating
information, namely the entropy of the underlying stochastic process. With a continuous source the situation
is considerably more involved. In the first place a continuously variable quantity can assume an infinite
number of values and requires, therefore, an infinite number of binary digits for exact specification. This
means that to transmit the output of a continuous source with exact recovery at the receiving point requires,

in general, a channel of infinite capacity (in bits per second). Since, ordinarily, channels have a certain
amount of noise, and therefore a finite capacity, exact transmission is impossible.
This, however, evades the real issue. Practically, we are not interested in exact transmission when we
have a continuous source, but only in transmission to within a certain tolerance. The question is, can we
assign a definite rate to a continuous source when we require only a certain fidelity of recovery, measured in
a suitable way. Of course, as the fidelity requirements are increased the rate will increase. It will be shown
that we can, in very general cases, define such a rate, having the property that it is possible, by properly
encoding the information, to transmit it over a channel whose capacity is equal to the rate in question, and
satisfy the fidelity requirements. A channel of smaller capacity is insufficient.
It is first necessary to give a general mathematical formulation of the idea of fidelity of transmission.
Consider the set of messages of a long duration, say T seconds. The source is described by giving the
probability density, in the associated space, that the source will select the message in questionP
/#28 x/#29 .Ag i v e n
communication system is described (from the external point of view) by giving the conditional probability
P
x
/#28 y/#29 that if message x is produced by the source the recovered message at the receiving point will bey.T h e
system as a whole (including source and transmission system) is described by the probability functionP/#28 x/; y/#29
of having message x and final output y. If this function is known, the complete characteristics of the system
from the point of view of fidelity are known. Any evaluation of fidelity must correspond mathematically
to an operation applied to P/#28 x/; y/#29 . This operation must at least have the properties of a simple ordering of
systems; i.e., it must be possible to say of two systems represented byP1
/#28 x/; y/#29 and P2
/#28 x/; y/#29 that, according to
our fidelity criterion, either (1) the first has higher fidelity, (2) the second has higher fidelity, or (3) they have
equal fidelity. This means that a criterion of fidelity can be represented by a numerically valued function:
v
/,
P/#28 x/; y/#29
/#01
whose argument ranges over possible probability functionsP/#28 x/; y/#29 .
We will now show that under very general and reasonable assumptions the function v
/,
P/#28 x/; y/#29
/#01
can be
written in a seemingly much more specialized form, namely as an average of a function /#1A /#28 x/; y/#29 over the set
of possible values of x and y:
v
/,
P/#28 x/; y/#29
/#01
/=
ZZ
P/#28 x/; y/#29 /#1A /#28 x/; y/#29 dxdy /:
To obtain this we need only assume (1) that the source and system are ergodic so that a very long sample
will be, with probability nearly 1, typical of the ensemble, and (2) that the evaluation is "reasonable" in the
sense that it is possible, by observing a typical input and output x
1 and y1, to form a tentative evaluation
on the basis of these samples; and if these samples are increased in duration the tentative evaluation will,
with probability 1, approach the exact evaluation based on a full knowledge of P/#28 x/; y/#29 . Let the tentative
evaluation be /#1A /#28 x/; y/#29 . Then the function /#1A /#28 x/; y/#29 approaches (as T /! ∞ ) a constant for almost all /#28 x/; y/#29 which
are in the high probability region corresponding to the system:
/#1A /#28 x/; y/#29 /! v
/,
P/#28 x/; y/#29
/#01
and we may also write
/#1A /#28 x/; y/#29 /!
ZZ
P/#28 x/; y/#29 /#1A /#28 x/; y/#29 dxdy
since
ZZ
P/#28 x/; y/#29 dxdy /= 1/:
This establishes the desired result.
The function /#1A /#28 x/; y/#29 has the general nature of a "distance" betweenx and y.9 It measures how undesirable
it is (according to our fidelity criterion) to receive y when x is transmitted. The general result given above
can be restated as follows: Any reasonable evaluation can be represented as an average of a distance function
over the set of messages and recovered messages x and y weighted according to the probability P
/#28 x/; y/#29 of
getting the pair in question, provided the duration T of the messages be taken sufficiently large.
The following are simple examples of evaluation functions:
9It is not a "metric" in the strict sense, however, since in general it does not satisfy either/#1A /#28 x/; y/#29/= /#1A /#28 y/; x/#29 or /#1A /#28 x/; y/#29/+ /#1A /#28 y/; z/#29 /#15 /#1A /#28 x/; z/#29 .

1. R.M.S. criterion.
v /=
/,
x/#28 t/#29 /, y/#28 t/#29
/#01
/:
In this very commonly used measure of fidelity the distance function /#1A /#28 x/; y/#29 is (apart from a constant
factor) the square of the ordinary Euclidean distance between the points x and y in the associated
function space.
/#1A /#28 x/; y/#29/=
T
Z
T
/#02
x/#28 t/#29 /, y/#28 t/#29
/#03
2 dt/:
2. Frequency weighted R.M.S. criterion. More generally one can apply different weights to the different
frequency components before using an R.M.S. measure of fidelity. This is equivalent to passing the
difference x/#28 t/#29 /, y/#28 t/#29 through a shaping filter and then determining the average power in the output.
Thus let
e/#28 t/#29/= x/#28 t/#29 /, y/#28 t/#29
and
f /#28 t/#29/=
Z
∞
/, ∞
e/#28 /#1C /#29 k/#28 t /, /#1C /#29 d/#1C
then
/#1A /#28 x/; y/#29/=
T
Z
T
f /#28 t/#29
2 dt/:
3. Absolute error criterion.
/#1A /#28 x/; y/#29/=
T
Z
T
/#0C
/#0C
x/#28 t/#29 /, y/#28 t/#29
/#0C
/#0C
dt/:
4. The structure of the ear and brain determine implicitly an evaluation, or rather a number of evaluations,
appropriate in the case of speech or music transmission. There is, for example, an "intelligibility"
criterion in which /#1A /#28 x/; y/#29 is equal to the relative frequency of incorrectly interpreted words when
message x/#28 t/#29 is received asy/#28 t/#29 . Although we cannot give an explicit representation of/#1A /#28 x/; y/#29 in these
cases it could, in principle, be determined by sufficient experimentation. Some of its properties follow
from well-known experimental results in hearing, e.g., the ear is relatively insensitive to phase and the
sensitivity to amplitude and frequency is roughly logarithmic.
5. The discrete case can be considered as a specialization in which we have tacitly assumed an evaluation
based on the frequency of errors. The function
/#1A /#28 x/; y/#29 is then defined as the number of symbols in the
sequence y differing from the corresponding symbols in x divided by the total number of symbols in
x.
28. T HE RATE FOR A SOURCE RELATIVE TO A FIDELITY EVA L UAT I O N
We are now in a position to define a rate of generating information for a continuous source. We are given
P/#28 x/#29 for the source and an evaluation v determined by a distance function /#1A /#28 x/; y/#29 which will be assumed
continuous in both x and y. With a particular system P/#28 x/; y/#29 the quality is measured by
v /=
ZZ
/#1A /#28 x/; y/#29 P/#28 x/; y/#29 dxdy /:
Furthermore the rate of flow of binary digits corresponding to P/#28 x/; y/#29 is
R /=
ZZ
P/#28 x/; y/#29 log P/#28 x/; y/#29
P/#28 x/#29 P/#28 y/#29
dxdy /:
We define the rate R1 of generating information for a given qualityv1 of reproduction to be the minimum of
R when we keep v fixed at v1 and vary Px
/#28 y/#29 .T h a ti s :
R1
/= Min
Px
/#28 y/#29
ZZ
P/#28 x/; y/#29 log P/#28 x/; y/#29
P/#28 x/#29 P/#28 y/#29
dxdy

subject to the constraint:
v1
/=
ZZ
P/#28 x/; y/#29 /#1A /#28 x/; y/#29 dxdy /:
This means that we consider, in effect, all the communication systems that might be used and that
transmit with the required fidelity. The rate of transmission in bits per second is calculated for each one
and we choose that having the least rate. This latter rate is the rate we assign the source for the fidelity in
question.
The justification of this definition lies in the following result:
Theorem 21:
If a source has a rate R1 for a valuation v1 it is possible to encode the output of the source
and transmit it over a channel of capacity C with fidelity as near v1 as desired provided R1
/#14 C. This is not
possible if R1
/#3E C.
The last statement in the theorem follows immediately from the definition of R1 and previous results. If
it were not true we could transmit more than C bits per second over a channel of capacity C. The first part
of the theorem is proved by a method analogous to that used for Theorem 11. We may, in the first place,
divide the /#28 x/; y/#29 space into a large number of small cells and represent the situation as a discrete case. This
will not change the evaluation function by more than an arbitrarily small amount (when the cells are very
small) because of the continuity assumed for
/#1A /#28 x/; y/#29 . Suppose that P1
/#28 x/; y/#29 is the particular system which
minimizes the rate and gives R1. We choose from the high probability y's a set at random containing
/#28 R1
/+ /#0F /#29 T
members where /#0F /! 0a s T /! ∞ . With large T each chosen point will be connected by a high probability
line (as in Fig. 10) to a set of x's. A calculation similar to that used in proving Theorem 11 shows that with
large T almost all x's are covered by the fans from the choseny points for almost all choices of the y's. The
communication system to be used operates as follows: The selected points are assigned binary numbers.
When a message x is originated it will (with probability approaching 1 as T
/! ∞ ) lie within at least one
of the fans. The corresponding binary number is transmitted (or one of them chosen arbitrarily if there are
several) over the channel by suitable coding means to give a small probability of error. SinceR1
/#14 C this is
possible. At the receiving point the corresponding y is reconstructed and used as the recovered message.
The evaluation v
/0
1 for this system can be made arbitrarily close to v1 by taking T sufficiently large.
This is due to the fact that for each long sample of message x/#28 t/#29 and recovered message y/#28 t/#29 the evaluation
approaches v1 (with probability 1).
It is interesting to note that, in this system, the noise in the recovered message is actually produced by a
kind of general quantizing at the transmitter and not produced by the noise in the channel. It is more or less
analogous to the quantizing noise in PCM.
29. T HE CALCULATION OF RATES
The definition of the rate is similar in many respects to the definition of channel capacity. In the former
R /= Min
Px
/#28 y/#29
ZZ
P/#28 x/; y/#29 log P/#28 x/; y/#29
P/#28 x/#29 P/#28 y/#29
dxdy
with P/#28 x/#29 and v1
/=
ZZ
P/#28 x/; y/#29 /#1A /#28 x/; y/#29 dxdy fixed. In the latter
C /= Max
P/#28 x/#29
ZZ
P/#28 x/; y/#29 log P/#28 x/; y/#29
P/#28 x/#29 P/#28 y/#29
dxdy
with Px
/#28 y/#29 fixed and possibly one or more other constraints (e.g., an average power limitation) of the form
K /=
R R
P/#28 x/; y/#29 /#15 /#28 x/; y/#29 dxdy .
A partial solution of the general maximizing problem for determining the rate of a source can be given.
Using Lagrange's method we consider
ZZ
/#14
P/#28 x/; y/#29 log P/#28 x/; y/#29
P/#28 x/#29 P/#28 y/#29
/+ /#16 P/#28 x/; y/#29 /#1A /#28 x/; y/#29/+ /#17 /#28 x/#29 P/#28 x/; y/#29
/#15
dxdy /:

The variational equation (when we take the first variation on P/#28 x/; y/#29 ) leads to
Py
/#28 x/#29/= B/#28 x/#29 e
/, /#15/#1A /#28 x/; y/#29
where /#15 is determined to give the required fidelity and B/#28 x/#29 is chosen to satisfy
Z
B/#28 x/#29 e
/, /#15/#1A /#28 x/; y/#29
dx /= 1/:
This shows that, with best encoding, the conditional probability of a certain cause for various received
y, Py
/#28 x/#29 will decline exponentially with the distance function /#1A /#28 x/; y/#29 between the x and y in question.
In the special case where the distance function/#1A /#28 x/; y/#29 depends only on the (vector) difference betweenx
and y,
/#1A /#28 x/; y/#29/= /#1A /#28 x /, y/#29
we have
Z
B/#28 x/#29 e
/, /#15/#1A /#28 x/, y/#29
dx /= 1/:
Hence B/#28 x/#29 is constant, say /#0B ,a n d
Py
/#28 x/#29/= /#0B e
/, /#15/#1A /#28 x/, y/#29
/:
Unfortunately these formal solutions are difficult to evaluate in particular cases and seem to be of little value.
In fact, the actual calculation of rates has been carried out in only a few very simple cases.
If the distance function/#1A /#28 x/; y/#29 is the mean square discrepancy betweenx and y and the message ensemble
is white noise, the rate can be determined. In that case we have
R /= Min
/#02
H/#28 x/#29 /, Hy
/#28 x/#29
/#03
/= H/#28 x/#29 /, MaxHy
/#28 x/#29
with N /= /#28 x /, y/#29
2.B u tt h eM a xHy
/#28 x/#29 occurs when y /, x is a white noise, and is equal toW1 log2 /#19 eN where
W1 is the bandwidth of the message ensemble. Therefore
R /= W1 log2 /#19 eQ /, W1 log2 /#19 eN
/= W1 log Q
N
where Q is the average message power. This proves the following:
Theorem 22: The rate for a white noise source of power Q and band W1 relative to an R.M.S. measure
of fidelity is
R /= W1 log Q
N
where N is the allowed mean square error between original and recovered messages.
More generally with any message source we can obtain inequalities bounding the rate relative to a mean
square error criterion.
Theorem 23: The rate for any source of band W1 is bounded by
W1 log Q1
N
/#14 R /#14 W1 log Q
N
where Q is the average power of the source, Q1 its entropy power and N the allowed mean square error.
The lower bound follows from the fact that the Max Hy
/#28 x/#29 for a given /#28 x /, y/#29
/= N occurs in the white
noise case. The upper bound results if we place points (used in the proof of Theorem 21) not in the best way
but at random in a sphere of radius
p
Q /, N.


## Acknowledgment

ACKNOWLEDGMENTS
The writer is indebted to his colleagues at the Laboratories, particularly to Dr. H. W. Bode, Dr. J. R. Pierce,
Dr. B. McMillan, and Dr. B. M. Oliver for many helpful suggestions and criticisms during the course of this
work. Credit should also be given to Professor N. Wiener, whose elegant solution of the problems of filtering
and prediction of stationary ensembles has considerably influenced the writer's thinking in this field.
APPENDIX 5
Let S1 be any measurable subset of the g ensemble, and S2 the subset of the f ensemble which gives S1
under the operation T .T h e n
S1
/= TS2
/:
Let H
/#15
be the operator which shifts all functions in a set by the time /#15 .T h e n
H
/#15
S1
/= H
/#15
TS2
/= TH
/#15
S2
since T is invariant and therefore commutes withH
/#15
. Hence if m/#5B S/#5D is the probability measure of the set S
m/#5B H
/#15
S1
/#5D/= m/#5B TH
/#15
S2
/#5D/= m/#5B H
/#15
S2
/#5D
/= m/#5B S2
/#5D/= m/#5B S1
/#5D
where the second equality is by definition of measure in the g space, the third since the f ensemble is
stationary, and the last by definition of g measure again.
To prove that the ergodic property is preserved under invariant operations, let S1 be a subset of the g
ensemble which is invariant underH
/#15
,a n dl e tS2 be the set of all functions f which transform into S1.T h e n
H
/#15
S1
/= H
/#15
TS2
/= TH
/#15
S2
/= S1
so that H
/#15
S2 is included in S2 for all /#15 .N o w ,s i n c e
m/#5B H
/#15
S2
/#5D/= m/#5B S1
/#5D
this implies
H
/#15
S2
/= S2
for all /#15 with m/#5B S2
/#5D /6/= 0/; 1. This contradiction shows that S1 does not exist.
APPENDIX 6
The upper bound, N3
/#14 N1
/+ N2, is due to the fact that the maximum possible entropy for a power N1
/+ N2
occurs when we have a white noise of this power. In this case the entropy power isN1
/+ N2.
To obtain the lower bound, suppose we have two distributions in n dimensions p/#28 xi
/#29 and q/#28 xi
/#29 with
entropy powers N1 and N2. What form should p and q have to minimize the entropy power N3 of their
convolution r/#28 xi
/#29 :
r/#28 xi
/#29/=
Z
p/#28 yi
/#29 q/#28 xi
/, yi
/#29 dyi
/:
The entropy H3 of r is given by
H3
/= /,
Z
r/#28 xi
/#29 logr/#28 xi
/#29 dxi
/:
We wish to minimize this subject to the constraints
H1
/= /,
Z
p/#28 xi
/#29 log p/#28 xi
/#29 dxi
H2
/= /,
Z
q/#28 xi
/#29 logq/#28 xi
/#29 dxi
/:

We consider then
U /= /,
Z
/#02
r/#28 x/#29 log r/#28 x/#29/+ /#15 p/#28 x/#29 log p/#28 x/#29/+ /#16 q/#28 x/#29 logq/#28 x/#29
/#03
dx
/#0E U /= /,
Z
/#02
/#5B 1 /+ logr/#28 x/#29/#5D /#0E r/#28 x/#29/+ /#15 /#5B 1 /+ log p/#28 x/#29/#5D /#0E p/#28 x/#29/+ /#16 /#5B 1 /+ logq/#28 x/#29/#5D /#0E q/#28 x/#29
/#03
dx/:
If p/#28 x/#29 is varied at a particular argument xi
/= si, the variation in r/#28 x/#29 is
/#0E r/#28 x/#29/= q/#28 xi
/, si
/#29
and
/#0E U /= /,
Z
q/#28 xi
/, si
/#29 logr/#28 xi
/#29 dxi
/, /#15 log p/#28 si
/#29/= 0
and similarly when q is varied. Hence the conditions for a minimum are
Z
q/#28 xi
/, si
/#29 logr/#28 xi
/#29 dxi
/= /, /#15 log p/#28 si
/#29
Z
p/#28 xi
/, si
/#29 logr/#28 xi
/#29 dxi
/= /, /#16 logq/#28 si
/#29 /:
If we multiply the first by p/#28 si
/#29 and the second by q/#28 si
/#29 and integrate with respect to si we obtain
H3
/= /, /#15 H1
H3
/= /, /#16 H2
or solving for /#15 and /#16 and replacing in the equations
H1
Z
q/#28 xi
/, si
/#29 logr/#28 xi
/#29 dxi
/= /, H3 log p/#28 si
/#29
H2
Z
p/#28 xi
/, si
/#29 logr/#28 xi
/#29 dxi
/= /, H3 logq/#28 si
/#29 /:
Now suppose p/#28 xi
/#29 and q/#28 xi
/#29 are normal
p/#28 xi
/#29/=
j Aij
j
n/= 2
/#28 2/#19 /#29
n/= 2 exp/,
2 ∑ Aij xixj
q/#28 xi
/#29/=
j Bij
j
n/= 2
/#28 2/#19 /#29
n/= 2 exp/,
2 ∑ Bij xixj
/:
Then r/#28 xi
/#29 will also be normal with quadratic form Cij . If the inverses of these forms are aij , bij , cij then
cij
/= aij
/+ bij
/:
We wish to show that these functions satisfy the minimizing conditions if and only if aij
/= Kbij and thus
give the minimum H3 under the constraints. First we have
logr/#28 xi
/#29/=
n
2 log 1
2/#19
j Cij
j/,
2 ∑ Cij xixj
Z
q/#28 xi
/, si
/#29 logr/#28 xi
/#29 dxi
/=
n
2 log 1
2/#19
j Cij
j/,
2 ∑ Cij sisj
/,
2 ∑ Cij bij
/:
This should equal
H3
H1
/#14
n
2 log 1
2/#19
j Aij
j/,
2 ∑ Aij sisj
/#15
which requires Aij
/=
H1
H3
Cij . In this case Aij
/=
H1
H2
Bij and both equations reduce to identities.


## Appendix

APPENDIX 7
The following will indicate a more general and more rigorous approach to the central definitions of commu-
nication theory. Consider a probability measure space whose elements are ordered pairs/#28 x/; y/#29 . The variables
x, y are to be identified as the possible transmitted and received signals of some long durationT . Let us call
the set of all points whose x belongs to a subset S1 of x points the strip over S1, and similarly the set whose
y belong to S2 the strip over S2.W ed i v i d ex and y into a collection of non-overlapping measurable subsets
Xi and Yi approximate to the rate of transmission R by
R1
/=
T ∑
i
P/#28 Xi
/; Yi
/#29 log P/#28 Xi
/; Yi
/#29
P/#28 Xi
/#29 P/#28 Yi
/#29
where
P/#28 Xi
/#29 is the probability measure of the strip over Xi
P/#28 Yi
/#29 is the probability measure of the strip overYi
P/#28 Xi
/; Yi
/#29 is the probability measure of the intersection of the strips/:
A further subdivision can never decreaseR1.F o rl e tX1 be divided into X1
/= X
/0
/+ X
/0 /0
1 and let
P/#28 Y1
/#29/= aP /#28 X1
/#29/= b /+ c
P/#28 X
/0
/#29/= bP /#28 X
/0
/; Y1
/#29/= d
P/#28 X
/0 /0
/#29/= cP /#28 X
/0 /0
/; Y1
/#29/= e
P/#28 X1
/; Y1
/#29/= d /+ e/:
Then in the sum we have replaced (for the X1, Y1 intersection)
/#28 d /+ e/#29 log d /+ e
a/#28 b /+ c/#29
by d log d
ab
/+ elog e
ac
/:
It is easily shown that with the limitation we have onb, c, d, e,
/#14
d /+ e
b /+ c
/#15
d/+ e
/#14
ddee
bdce
and consequently the sum is increased. Thus the various possible subdivisions form a directed set, with
R monotonic increasing with refinement of the subdivision. We may define R unambiguously as the least
upper bound for R1 and write it
R /=
T
ZZ
P/#28 x/; y/#29 log P/#28 x/; y/#29
P/#28 x/#29 P/#28 y/#29
dxdy /:
This integral, understood in the above sense, includes both the continuous and discrete cases and of course
many others which cannot be represented in either form. It is trivial in this formulation that if x and u are
in one-to-one correspondence, the rate from u to y is equal to that from x to y.I f v is any function of y (not
necessarily with an inverse) then the rate from x to y is greater than or equal to that from x to v since, in
the calculation of the approximations, the subdivisions of y are essentially a finer subdivision of those for
v. More generally if y and v are related not functionally but statistically, i.e., we have a probability measure
space /#28 y/; v/#29 ,t h e nR/#28 x/; v/#29 /#14 R/#28 x/; y/#29 . This means that any operation applied to the received signal, even though
it involves statistical elements, does not increaseR.
Another notion which should be defined precisely in an abstract formulation of the theory is that of
"dimension rate," that is the average number of dimensions required per second to specify a member of
an ensemble. In the band limited case 2 W numbers per second are sufficient. A general definition can be
framed as follows. Let f
/#0B
/#28 t/#29 be an ensemble of functions and let /#1A
T
/#5B f
/#0B
/#28 t/#29 /; f
/#0C
/#28 t/#29/#5D be a metric measuring

the "distance" from f
/#0B
to f
/#0C
over the time T (for example the R.M.S. discrepancy over this interval.) Let
N/#28 /#0F/; /#0E /; T /#29 be the least number of elements f which can be chosen such that all elements of the ensemble
apart from a set of measure /#0E are within the distance /#0F of at least one of those chosen. Thus we are covering
the space to within /#0F apart from a set of small measure /#0E . We define the dimension rate /#15 for the ensemble
by the triple limit
/#15 /= Lim
/#0E /! 0
Lim
/#0F /! 0
Lim
T /! ∞
logN/#28 /#0F/; /#0E /; T /#29
T log /#0F
/:
This is a generalization of the measure type definitions of dimension in topology, and agrees with the intu-
itive dimension rate for simple ensembles where the desired result is obvious.

