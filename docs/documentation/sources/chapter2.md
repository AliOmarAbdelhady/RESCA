<!-- Chapter 2, Literature Review and Background. Owner: Person 2 (Bela). Built by tools/build_report.py. -->
This chapter reviews research and operational systems relevant to the proposed RescueVision platform. It is organised around six questions that follow the platform’s features: how disaster information is presented, how affected areas are understood in 2D and 3D, how damage cost is estimated, how people who need assistance are found and followed, how hazards affect movement, and how organisations coordinate a response. Each theme compares several sources, notes where they agree and differ, and ends with what the findings mean for RescueVision. Capabilities that RescueVision proposes are described as aims to be tested, not as demonstrated advantages.

## REVIEW METHOD

Sources were found in IEEE Xplore, the ACM Digital Library, MDPI, Springer, Nature Scientific Data, arXiv and Google Scholar, and in the official documentation of operational systems. A source was included when it met one of three conditions: it was a peer-reviewed study of a technique the platform depends on, a public dataset the project uses or plans to use, or an official description of a comparable system. Each entry was checked against its publisher, DOI or official page before it was accepted. Appendix D records the search terms, the date of each search, the sources selected and the reason for selection, together with the team’s ranked list of candidate papers.

The project configuration names several models but has not yet produced trained results; the planned experiments are still pending. This chapter therefore reports what the source studies measured on their own benchmarks and states separately what still has to be measured on the project’s data.

## PRESENTING DISASTER INFORMATION

The literature agrees that responders need information that is fast, map-based and honest about its accuracy. It agrees less on how one display can support shared understanding across teams.

Endsley’s model of situation awareness separates perceiving the elements of a situation, understanding what they mean and projecting what happens next [@endsley]. It identifies attention and working memory as the limits on what an operator can absorb, so a display that lists raw detections leaves the hardest work, interpretation, to a user under stress. Wolbers and Boersma observed Dutch command teams building a common operational picture during exercises [@wolbers]. They concluded that the picture is better understood as a process of collective sensemaking than as a finished information product. The Sendai Framework also places understanding disaster risk first among its priorities [@sendai].

Operational mapping services show how damage information is delivered in practice. Voigt et al. describe how the German Aerospace Center produced rapid satellite maps after the 2004 Indian Ocean tsunami and the 2005 Pakistan earthquake, using imagery obtained through the International Charter Space and Major Disasters [@voigt]. The Copernicus Emergency Management Service formalises this into product types: a first estimate, a delineation of the affected extent and a grading of damage, each delivered as print-ready maps and as vector data [@copernicus]. These services establish a fixed damage legend, dated products and machine-readable layers as normal practice.

Presentation can also mislead. Kerle compared the satellite damage maps produced after the 2006 Yogyakarta earthquake with a ground survey [@kerle2010]. Detailed maps underestimated the damage and missed large areas, and grid-based maps understated how widespread it was; sparse imagery and cloud cover limited both. Kerle and Hoffman argue that collaborative damage mapping must be designed around the user’s cognitive tasks rather than assuming that maps are read as intended [@kerlehoffman]. SensePlace2 linked a map, a timeline and a text view of geolocated messages to support crisis situation awareness, but its evaluation involved eight participants, so it shows feasibility more than proven benefit [@senseplace].

The sources agree that the map is the shared view and that speed matters. They differ on whether a better product [@voigt], [@copernicus] or a better process between people [@wolbers], [@kerlehoffman] matters most. None of the operational products reviewed shows a confidence value for each building, although Kerle’s comparison shows that authoritative-looking maps can be wrong. For RescueVision, this supports dated layers, a fixed damage legend and exportable vector data, with model confidence and review status shown for every item. Whether that helps responders has to be tested with users.

## UNDERSTANDING AFFECTED AREAS IN 2D AND 3D

Deep learning on paired before-and-after imagery is now the standard research approach to building damage mapping. Drone imagery and 3D reconstruction add detail that satellites miss. The main open problem is whether a model trained on one event works on the next.

Dell’Acqua and Gamba’s survey of earthquake damage mapping separates estimating where damage is from estimating how severe it is, and compares the strengths and weaknesses of optical and radar data [@dellacqua]. The xBD dataset turned damage mapping into a shared benchmark. It pairs pre-event and post-event satellite images with building outlines and a four-level damage scale, and its final version contains 850,736 building annotations over 45,362 km² [@xbd]. RescueVision’s main pipeline is designed around xBD.

Fully convolutional networks (FCNs) showed how to train a network to produce a class for every pixel [@fcn]. U-Net added a decoder with skip connections that recover the detail lost as features are downsampled, which matters for building outlines [@unet]. Residual connections made deeper encoders trainable [@resnet], and EfficientNet scales depth, width and image resolution together [@efficientnet]. For change detection, Daudt et al. showed that Siamese fully convolutional networks, which pass both dates through matching branches, detect change accurately and run at least 500 times faster than earlier related methods [@daudt]. Weber and Kané reported that how the xBD task is framed, including fusing both dates inside the network, mattered as much as the choice of architecture; their approach ranked among the top xView2 results [@weber].

The Transformer replaced recurrence with attention [@transformer]. SegFormer applies a hierarchical Transformer encoder and a light decoder to segmentation [@segformer]. DINOv3 learns image features without labels and adds Gram anchoring to keep pixel-level features stable during long training; its authors release versions pretrained on satellite imagery [@dinov3]. Table 2-1 summarises the seven core studies, the figures they report and the limits on applying them here.

Table: Table 2-1: Core model studies and their applicability to RescueVision
| Study | Reported evidence in the source | Use in RescueVision and limit |
| FCN [@fcn] | End-to-end dense prediction; 62.2% mean IoU on PASCAL VOC 2012 | Basis of every pixel-level model in the design. Boundaries are coarse without a decoder. |
| U-Net [@unet] | Encoder–decoder with skip connections; won the ISBI 2015 cell-tracking challenge with few training images | Configured for building masks, paired damage masks and Siamese change detection. Not yet evaluated on aerial imagery. |
| ResNet [@resnet] | Residual learning; 3.57% top-5 error on ImageNet with an ensemble | ResNet34 encoder in the building and change models. Pretrained on ground-level photographs. |
| EfficientNet [@efficientnet] | Compound scaling; B7 reached 84.3% top-1 on ImageNet while being 8.4 times smaller than the best earlier network | B3 encoder for six-channel damage segmentation and crop classification. The six-channel input needs an adapted first layer. |
| Transformer [@transformer] | Attention-only architecture; 28.4 BLEU on English–German translation | Architectural basis of SegFormer and DINO models. No imagery benchmark. |
| SegFormer [@segformer] | Hierarchical Transformer encoder; 84.0% mIoU on Cityscapes validation (B5) | Configured for FloodNet, building and damage masks. Street-scene results do not transfer automatically to aerial views. |
| DINOv3 [@dinov3] | Self-supervised features with Gram anchoring; versions pretrained on 493 million satellite images | Candidate backbone for the building-crop classifier. The current configuration uses DINOv2 [@dinov2]; one backbone must be chosen and compared with EfficientNet-B3 on the same crops. |

Benchmark scores do not guarantee field performance. Nex et al. tested a state-of-the-art convolutional network under operational conditions, with little or no training on the new site and under time limits, and showed that accuracy does not transfer automatically to a new event [@nex]. Drone datasets help when no pre-event image exists. FloodNet provides high-resolution drone images from Hurricane Harvey with pixel labels for flooded buildings and roads [@floodnet], and RescueNet provides 4,494 drone images from Hurricane Michael labelled in ten classes, including four building-damage levels and separate road-clear and road-blocked classes [@rescuenet]. Each covers a single hurricane, so transfer to earthquakes or other regions is not established.

Three-dimensional data adds evidence that a top-down view hides. Vetrivel et al. combined convolutional features with 3D point cloud features from oblique aerial images; accuracy rose from about 91% to about 94%, and the gain on unseen sites reached 7 percentage points [@vetrivel]. Fernandez Galarreta et al. used a drone point cloud to find structural collapse and oblique images to grade façades and roofs, as support for an analyst rather than a replacement [@galarreta]. Map position also has limits. Turner et al. reported 65–120 cm absolute error for drone mosaics georeferenced from camera positions alone and about 10–15 cm with ground control points [@turner], and the OpenDroneMap documentation warns that drone GPS alone is typically accurate to 2–6 m [@odm].

The sources agree that before-and-after comparison is stronger than single-image analysis when both images exist, and that 3D adds evidence of collapse. The open problems are transfer between events, the ambiguity between neighbouring damage levels and map position error. For RescueVision, this supports keeping both a before/after path and a post-event-only path, labelling which one produced each grade, reporting results on held-out events, and measuring map position error rather than assuming it.

## ESTIMATING DAMAGE COST

Feature F1 adds an indicative restoration cost to each damage grade. The established reference for this kind of estimate is the FEMA Hazus methodology [@hazus]. Hazus estimates direct building loss by combining the probability of each structural damage state (slight, moderate, extensive and complete) with a repair cost expressed as a ratio of the replacement cost for the building’s occupancy class. The method is designed for planning-level estimates over many buildings, not for valuing a single property.

Two limits follow for RescueVision. First, the xBD grades are visual categories, not the engineering damage states that Hazus uses, so any mapping between them is an assumption that must be stated. Second, Hazus replacement costs describe United States building stock; the unit costs and repair ratios for another region have to be collected locally. Kerle’s finding that remote-sensing damage maps can understate damage [@kerle2010] also means that a cost total inherits any error in the grades beneath it.

For RescueVision, a cost range per building, with its assumptions visible and editable, follows the Hazus approach while avoiding false precision. The estimate is for prioritisation and planning; it is not an engineering survey or an insurance valuation.

## IDENTIFYING AND FOLLOWING PEOPLE WHO NEED ASSISTANCE

Research finds people in need through two channels: what people report themselves, and what sensors observe. Each channel finds people the other misses, and neither finds people who are both silent and hidden.

Okolloh describes how Ushahidi was built during Kenya’s 2007–08 election crisis so that citizens could report incidents by SMS and the web and see them on a shared map [@okolloh]. Imran et al. survey methods for processing social media in emergencies and identify three persistent problems: information overload, judging which messages are credible, and prioritising message types such as requests for help [@imran]. Self-reporting scales to many people but reaches only those with a working phone and network.

Unmanned aerial vehicles (UAVs) can survey an affected area and relay communication for survivors [@erdelj]. Detecting people from the air is harder than in ground-level photographs because people are small, seen from above and often partly hidden. Table 2-2 compares the main detector families that recur in this work.

Table: Table 2-2: Object detector families relevant to aerial person detection
| Detector family | How it works | Evidence relevant to RescueVision |
| Two-stage: Faster R-CNN [@fasterrcnn] | A region proposal network suggests candidate boxes, and a second stage classifies and refines them. | Accurate on small objects but slower; one of the four detectors compared on search-and-rescue imagery [@sard]. |
| One-stage with focal loss: RetinaNet [@focalloss] | Predicts boxes in one pass and down-weights easy background examples so that rare objects are not swamped. | Addresses the imbalance between few people and much background in aerial images. |
| One-stage real-time: YOLOv4 [@yolov4] | Predicts boxes and classes in a single network pass optimised for speed. | Chosen in the SARD study for its balance of speed, accuracy and few false detections [@sard]. |
| Transformer-based: RT-DETR [@rtdetr] | An end-to-end Transformer detector that removes hand-tuned post-processing. | Reports 53.1% AP on COCO at 108 frames per second (R50); not yet tested on disaster imagery. |

Sambolek and Ivasic-Kos built the SARD dataset of 1,981 drone images of people simulating exhausted or injured hikers and compared Faster R-CNN, YOLOv4, RetinaNet and Cascade R-CNN; they chose YOLOv4 and tested its robustness to fog, snow and motion blur [@sard]. Božić-Štulić et al. reported a detection rate of 88.9% at a precision of 34.8% on the HERIDAL search-and-rescue images [@heridal], which shows that a high detection rate can come with many false alarms. Lygouras et al. ran a person detector on board a rescue drone to locate swimmers and release a flotation device [@lygouras]. VisDrone is a general drone benchmark recorded over Chinese cities, not a disaster dataset, but it shows that detecting and tracking small people from the air remains difficult [@visdrone]. ByteTrack improves tracking by also associating low-confidence detections, which reduces broken tracks when people are partly hidden [@bytetrack].

A detection must also be placed on the map. Liu et al. show that single-image geolocation is sensitive to errors in drone position, camera angle and target height, and that combining several views improves accuracy [@liu]; the GPS tag of a photograph gives the camera’s position, not the person’s. People buried under rubble cannot be seen by RGB cameras at all. The MURMUR radar from MIT Lincoln Laboratory detects breathing through concrete and debris [@murmur], but its public description is a project page, so its field accuracy is not established by the source.

The sources agree that no single channel finds everyone and that aerial detections produce false alarms. For RescueVision, this supports treating every detection as a candidate for human review, attaching a position uncertainty in metres to each one, and bringing citizen requests, responder reports and drone detections into one list of assistance cases. Detection of people under rubble is outside the scope of the aerial feature.

## HAZARDS AND MOVEMENT

Road blockage, flooding and shortest-path routing are each well studied. Research rarely joins them, and few systems treat the interaction between hazards as a hazard in its own right.

Rastiveis et al. compared a pre-event road map with post-earthquake satellite images of Port-au-Prince and labelled roads as blocked or open; all 60 roads in a 1.2 × 0.8 km test area were labelled correctly, a small test that depends on an up-to-date road map [@rastiveis]. RescueNet labels road-clear and road-blocked pixels directly in drone images [@rescuenet], and FloodNet labels flooded roads [@floodnet]. Yin et al. coupled a flood model with the road network of central Shanghai and found that road disruption depends on rainfall pattern, drainage and terrain, and grows non-linearly with flood severity [@yin].

Routing research supplies the algorithms. Dijkstra’s algorithm finds shortest paths in a weighted graph [@dijkstra], A\* speeds the search with a distance estimate [@astar], and D\* Lite repairs an existing route when part of the map changes instead of planning again from scratch [@dstarlite]. Yuan and Wang modelled emergency routing in which road speed falls as a disaster spreads [@yuanwang]. pgRouting provides these algorithms inside a spatial database [@pgrouting].

Hazards also interact. Gill and Malamud reviewed 21 natural hazards and identified 90 interactions in which one hazard triggers or increases the likelihood of another [@gillmalamud]. Kappes et al. explain why analysing several hazards together is harder than analysing each alone, because both the hazard levels and the vulnerability to each process interact [@kappes]. Public guidance warns that floodwater can contain downed power lines and advises against entering or driving through water where lines are down [@cdcflood]. This combination of floodwater and live electrical infrastructure is the scenario behind the proposed Electrified Water alert.

The sources agree that blocked and flooded roads should be treated as costs or exclusions in a road network and that conditions change after an image is taken. They differ in where road state comes from: maps and imagery, learned segmentation or flood models. None of the routing studies reviewed carries the uncertainty of a detected road state into the route, and none of the mapping systems reviewed raises an alert when two hazards combine. For RescueVision, this supports routing per vehicle with closed and too-deep segments excluded, re-planning when a road closes, treating an unknown power state as energised, and reporting how often a blocked road is wrongly marked safe.

## COORDINATION BETWEEN EMERGENCY ORGANIZATIONS

Coordination research finds that failures come more from organisations not sharing understanding than from missing technology. Operational systems exist for imagery, volunteers and rescue teams, but each covers one part of the work.

Comfort analysed the response to Hurricane Katrina through cognition, communication, coordination and control, and argued that coordination broke down when agencies did not share an understanding of the risk [@comfort]. Bharosa et al. combined a literature review with observations and a survey from multi-agency exercises and grouped the obstacles to information sharing at community, agency and individual levels [@bharosa]. The National Incident Management System gives responding organisations common terminology and an incident command structure [@nims]. Humanitarian data-responsibility guidance adds that sharing sensitive data can cause harm, so access must follow purpose and role [@ocha].

Operational mechanisms cover different parts of the work. The International Charter Space and Major Disasters lets an authorised national agency request satellite imagery during the immediate response [@charter]. The HOT Tasking Manager splits a mapping area into small tasks for volunteers, and experienced mappers validate each task [@hot]. The INSARAG Guidelines set international standards for urban search-and-rescue teams, including a coordination cell and a shared marking system for searched structures [@insarag]. Sahana is an open-source disaster management system developed in Sri Lanka and described with a deployment case study [@sahana].

The sources agree that coordination depends on shared standards and shared understanding, not only on software. For RescueVision, this supports one shared incident that a lead agency opens and other agencies join, common role names across agencies, access limited to agencies whose participation is active, and outputs that can be exported to partners. Whether this improves coordination is a hypothesis that would need a tabletop exercise or a field trial to test.

## RELATED SYSTEMS AND USE CONTEXT

Table 2-3 compares comparable systems using only what their sources document. Information a source does not give is marked as not established by the source.

Table: Table 2-3: Related systems and their documented capabilities
| System | Purpose and intended users | Relevant capabilities | Documented limitations |
| Copernicus EMS Rapid Mapping [@copernicus] | On-demand satellite maps after a disaster; users not established by the source consulted. | First-estimate, delineation and damage-grading maps; print maps and vector data. | Depends on post-event image acquisition; pre-event reference maps only outside Europe. |
| International Charter [@charter] | Free satellite data for major disasters; authorised national agencies and United Nations users. | A 24-hour request point; member agencies task satellites; partners produce maps. | Immediate response only; no slow-onset or armed-conflict disasters. |
| HOT Tasking Manager [@hot] | Coordinated volunteer mapping in OpenStreetMap; volunteers and organisations. | Splits an area into tasks; validation of each task by experienced mappers. | Not established by the source. |
| Ushahidi [@ushahidi], [@okolloh] | Collection and mapping of crowdsourced reports; deploying organisations and the public. | SMS, email and web intake; surveys and mobile apps; review workflows; map view. | Not established by the source; crowdsourced messages in general face overload and credibility problems [@imran]. |
| Sahana [@sahana] | Open-source disaster management; users not established by the source consulted. | Relief-management modules and a deployment case study. | Not established by the source consulted. |
| INSARAG Guidelines [@insarag] | Standards for international urban search and rescue; rescue teams and coordination centres. | Coordination cell, information management and a marking system for searched structures. | A methodology, not software. |
| MURMUR radar [@murmur] | Detection of breathing survivors under rubble; first responders. | Robot-mounted radar reporting burial depth and breathing rate. | Field accuracy not established by the source. |
| SensePlace2 [@senseplace] | Map-based analysis of crisis messages; analysts. | Linked map, timeline and text views. | Evaluated with eight users only. |

Table 2-4 shows which of the RescueVision features each system addresses according to its source. The RescueVision row lists proposed capabilities that remain to be built and tested.

Table: Table 2-4: Coverage of the RescueVision features by related systems
| System | Damage and cost (F1) | Map and routes (F2) | People (F3, F4) | Compound hazards (F5) | Reports and sharing (F6) |
| Copernicus EMS | Damage grading | Maps only | Not established | Not established | Map and vector products |
| International Charter | Through partner maps | Maps only | No | No | Data delivery |
| HOT Tasking Manager | No | Map data | No | No | Open map data |
| Ushahidi | No | Report map | Self-reports | No | Report workflows |
| INSARAG Guidelines | No | No | Search and marking | No | Coordination procedures |
| MURMUR | No | No | Buried, breathing people | No | No |
| RescueVision (proposed) | Proposed | Proposed | Proposed | Proposed | Proposed |

The intended users of RescueVision are local and national agencies (Government, Police, Emergency Medical Services and Fire) that fly their own drones or receive satellite imagery and need to act on it together. The international services above deliver satellite maps to national authorities within hours [@copernicus], [@charter], but the sources reviewed do not describe an open platform that turns that imagery into shared damage, people, hazard and route records for several local agencies at once. A market assessment of adopters, prices and procurement was outside the evidence collected for this report. One practical constraint applies to any use beyond research: the Maxar Open Data imagery used in the prototype is licensed for non-commercial use [@maxar].

## RESEARCH GAP

The reviewed research and systems treat damage mapping, finding people, movement planning and coordination separately, and they rarely show users how uncertain each output is. No source reviewed evaluates one platform in which several agencies share a single incident and every AI result keeps its provenance until a person confirms it. Four specific gaps support this statement.

First, damage models are not shown to transfer to new events: accuracy drops under operational conditions [@nex], the drone datasets each cover a single hurricane [@floodnet], [@rescuenet], and authoritative-looking maps have understated real damage [@kerle2010]. Second, provenance and uncertainty are rarely visible: none of the operational products in Table 2-3 shows confidence or review status per item, and detection position error is seldom reported with detection accuracy [@liu]. Third, people-finding channels are not joined: self-reports [@imran], [@okolloh], aerial detections [@sard] and rescue procedures [@insarag] sit in separate systems, and the hand-over between agencies is a known obstacle [@bharosa]. Fourth, compound hazards are recognised in hazard research [@gillmalamud], [@kappes] but not acted on in the routing and mapping systems reviewed, which do not close roads or warn teams when floodwater meets live power lines.

RescueVision responds with one shared multi-agency incident, AI results that keep their model version and remain candidates until a person confirms them, assistance cases that join drone, responder and citizen sources, and a rule-based compound hazard alert that closes roads and re-plans routes. Section 3.2 turns these responses into requirements, Section 3.3 designs them, and Chapter 4 reports the limited evidence produced so far. Whether they close the gaps can only be shown by the evaluations described in Chapter 5.
